import csv
import codecs
import json
from datetime import datetime
from ivetl.celery import app
from ivetl.models import PublishedArticle, ArticleCitations, PublisherVizorUpdates
from ivetl.pipelines.task import Task
from ivetl.connectors.crossref import CrossrefConnector

@app.task
class InsertScopusIntoCassandra(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        file = task_args['input_file']
        total_count = task_args['count']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0
        updated_date = datetime.today()

        # For reliability, we retrieve the (publication) citation date from Crossref
        crossref = CrossrefConnector("", "", tlogger)

        with codecs.open(file, encoding="utf-16") as tsv:

            for line in csv.reader(tsv, delimiter="\t"):

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                if count == 1:
                    continue

                publisher_id = line[0]
                doi = line[1]
                citations = json.loads(line[2])

                for data in citations:

                    citation_doi = data.get('doi')
                    if not citation_doi:
                        tlogger.info('No citation DOI found, skipping...')
                        continue

                    if not isinstance(citation_doi, str):
                        tlogger.info('citation doi is not of type string, skipping... ' + str(type(citation_doi)))
                        continue

                    citation_date = data.get('date')
                    if isinstance(citation_date, str):
                        try:
                            citation_date = datetime.strptime(citation_date[:10], '%Y-%m-%d')
                        except ValueError:
                            tlogger.info('Badly formatted date for citation %s, skipping...' % citation_doi)
                            continue

                    if not isinstance(citation_date, datetime):
                        tlogger.info('No date for citation %s, or not a datetime object, skipping...' % citation_doi)
                        continue

                    # unfortunately we have to retrieve the publication date from Crossref, slowing us down.
                    crossref_article = crossref.get_article(citation_doi)
                    cr_date = crossref_article['date']
                    if cr_date and citation_date != cr_date:
                        tlogger.info('MAG and Crossref dates differ: {1} != {2}'.format(citation_doi, cr_date))
                        citation_date = cr_date

                    non_list_fields = [
                        'scopus_id',
                        'first_author',
                        'issue',
                        'journal_issn',
                        'journal_title',
                        'pages',
                        'title',
                        'volume',
                    ]

                    # check that we don't have any of the weird malformed list values from scopus
                    skip_for_unexpected_list = False
                    for field in non_list_fields:
                        if type(data.get(field)) == list:
                            tlogger.info('Badly formatted value for %s from scopus, skipping...' % field)
                            skip_for_unexpected_list = True

                    if skip_for_unexpected_list:
                        continue

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

                tlogger.info(str(count-1) + ". " + publisher_id + " / " + doi + ": Inserted " + str(len(citations)) + " citations.")

            tsv.close()

            PublisherVizorUpdates.create(
                publisher_id=publisher_id,
                vizor_id=pipeline_id,
                updated=updated_date,
            )

        task_args['count'] = count
        return task_args
