import codecs
import csv
import json
import sys
import threading

from datetime import datetime
from ivetl.common import common
from ivetl.celery import app
from ivetl.connectors.crossref import CrossrefConnector
from ivetl.models import PublishedArticle, ArticleCitations, PublisherVizorUpdates
from ivetl.pipelines.task import Task

@app.task
class InsertScopusIntoCassandra(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        file = task_args['input_file']

        total_count = 0
        count = 0
        count_lock = threading.Lock()
        updated_date = datetime.today()

        # For reliability, we retrieve the (publication) citation date from Crossref
        crossref = CrossrefConnector("", "", tlogger)

        all_entries= []
        with codecs.open(file, encoding="utf-16") as tsv:
            lineno = 0
            for line in csv.reader(tsv, delimiter="\t"):
                lineno += 1

                if lineno == 1:
                    continue

                if line[0] != publisher_id:
                    tlogger.info("skipping %s:%i: publisher_id %s does not match expected value %s" % (file, lineno, line[0], publisher_id))
                    continue

                try:
                    citations = json.loads(line[2])
                    n = len(citations)
                    if n > 0:
                        total_count += n
                    else:
                        continue
                except:
                    tlogger.info("skipping %s:%i: unable to parse json: %s" % (file, lineno, sys.exc_info()))

                entry = {
                    "doi": common.normalizedDoi(line[1]),
                    "citations": citations,
                    "lineno":lineno
                }

                all_entries.append(entry)
            tsv.close()

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)
        tlogger.info("queued %i entries" % (total_count))

        def process_entries(entries_for_this_thread):
            nonlocal count;

            for entry in entries_for_this_thread:
                doi = entry["doi"]
                citations = entry["citations"]
                lineno = entry["lineno"]

                for data in citations:
                    with count_lock:
                        count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    citation_doi = data.get('doi')
                    if not citation_doi:
                        continue

                    if not isinstance(citation_doi, str):
                        tlogger.info('citation doi is not of type string, skipping... %s' % (str(type(citation_doi))))
                        continue

                    citation_date = data.get('date')
                    if isinstance(citation_date, str):
                        try:
                            citation_date = datetime.strptime(citation_date[:10], '%Y-%m-%d')
                        except ValueError:
                            tlogger.info('Badly formatted date for citation %s, skipping...' % (citation_doi))
                            continue

                    if not isinstance(citation_date, datetime):
                        tlogger.info('No date for citation %s, or not a datetime object, skipping...' % (citation_doi))
                        continue

                    # unfortunately we have to retrieve the publication date from Crossref, slowing us down.
                    crossref_article = crossref.get_article(citation_doi)
                    cr_date = crossref_article['date'] if crossref_article else citation_date
                    if citation_date != cr_date:
                        tlogger.info('DOI {0} MAG date {1} and Crossref date {2} differ'.format(citation_doi, citation_date, cr_date))
                        citation_date = cr_date

                    # note this try-except should probably be removed when we're satisfied there are no bugs
                    try:
                        ArticleCitations.create(
                            publisher_id=publisher_id,
                            article_doi=doi,
                            citation_doi=citation_doi,
                            citation_scopus_id=data['scopus_id'],
                            citation_date=citation_date,
                            citation_first_author=data['first_author'],
                            citation_issue=data['issue'],
                            citation_journal_issn=data['journal_issn'],
                            citation_journal_title=data['journal_title'],
                            citation_pages=data['pages'],
                            citation_source_scopus=True,
                            citation_title=data['title'],
                            citation_volume=data['volume'],
                            citation_count=1,
                            updated=updated_date,
                            created=updated_date,
                            is_cohort=data['is_cohort']
                        )
                    except:
                        tlogger.error('Exception when inserting citation for %s (%s)' % (doi, citation_doi))
                        tlogger.error(data)
                        raise

                PublishedArticle.objects(
                    publisher_id=publisher_id,
                    article_doi=doi
                ).update(
                    citations_updated_on=updated_date
                )

                tlogger.info("{0} / {1}: Processed {2} citations.".format(publisher_id, doi, len(citations)) )
        # end of def process_entries

        self.run_pipeline_threads(process_entries, all_entries, tlogger=tlogger)

        PublisherVizorUpdates.create(
            publisher_id=publisher_id,
            vizor_id=pipeline_id,
            updated=updated_date,
        )

        task_args['count'] = count
        return task_args
