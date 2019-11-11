import codecs
import csv
import json
import os

from ivetl.common import common
from ivetl.celery import app
from ivetl.connectors.base import MaxTriesAPIError
from ivetl.connectors.scopus import ScopusConnector
from ivetl.models import PublisherMetadata, PublishedArticle
from ivetl.pipelines.task import Task


@app.task
class ScopusIdLookupTask(Task):
    MAX_ERROR_COUNT = 100

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        file = task_args['input_file']
        total_count = task_args['count']

        target_file_name = work_folder + "/" + publisher_id + "_" + "scopuscitationlookup" + "_" + "target.tab"

        already_processed = set()

        # if the file exists, read it in assuming a job restart
        if os.path.isfile(target_file_name):
            with codecs.open(target_file_name, encoding='utf-16') as tsv:
                for line in csv.reader(tsv, delimiter='\t'):
                    if line and len(line) == 4 and line[0] != 'PUBLISHER_ID':
                        doi = common.normalizedDoi(line[1])
                        already_processed.add(doi)

        if already_processed:
            tlogger.info('Found %s existing items to reuse' % len(already_processed))

        target_file = codecs.open(target_file_name, 'a', 'utf-16')

        if not already_processed:
            target_file.write('PUBLISHER_ID\tDOI\tISSN\tDATA\n')

        pm = PublisherMetadata.objects.filter(publisher_id=publisher_id).first()
        # The Scopus connector now talks to the MAG-resolver
        mag = ScopusConnector(pm.scopus_api_keys)

        count = 0
        error_count = 0
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):
                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                if count == 1:
                    continue  # ignore the header

                publisher_id = line[0]
                doi = common.normalizedDoi(line[1])
                issn = line[2]
                data = json.loads(line[3])

                if doi in already_processed:
                    continue

                tlogger.info(str(count-1) + ". Retrieving Scopus Id for: " + doi)

                # If its already in the database, we don't have to check with scopus
                #existing_record = PublishedArticle.objects.filter(publisher_id=publisher_id, article_doi=doi).first()

                # Replacing scopus_id with MAG paper_id; must perform an initial mag.get_entry(doi) lookup,
                # existing_record check can be re-enabled after all scopus_ids have been replaced.
                existing_record = False

                if existing_record and existing_record.article_scopus_id and existing_record.scopus_subtype:
                    data['scopus_id_status'] = "DOI in Scopus"
                    data['scopus_id'] = existing_record.article_scopus_id
                    data['scopus_citation_count'] = existing_record.scopus_citation_count
                    data['scopus_subtype'] = existing_record.scopus_subtype
                    tlogger.info("Scopus Id already retrieved in previous run")

                else:
                    try:
                        mag_paper_id, mag_citations, scopus_subtype = mag.get_entry(
                            doi,
                            tlogger,
                            data.get('ISSN'),
                            data.get('volume'),
                            data.get('issue'),
                            data.get('page')
                        )

                        if mag_paper_id and mag_citations is not None:
                            data['scopus_id_status'] = "DOI in Scopus"
                            data['scopus_id'] = mag_paper_id
                            data['scopus_citation_count'] = mag_citations
                            data['scopus_subtype'] = scopus_subtype
                            tlogger.info("DOI {0} is MAG PaperId {1}, with {2} citations"
                                        .format(doi, mag_paper_id, mag_citations))
                        else:
                            tlogger.info("No MAG PaperId found for DOI: " + doi)
                            data['scopus_id_status'] = "No DOI in Scopus"
                            data['scopus_id'] = ''

                    except MaxTriesAPIError:
                        tlogger.info("MAG API failed with MaxTriesAPIError.")
                        data['scopus_id'] = ''
                        data['scopus_id_status'] = "Scopus API failed"
                        error_count += 1

                row = "%s\t%s\t%s\t%s\n" % (publisher_id, doi, issn, json.dumps(data))

                target_file.write(row)

                if error_count >= self.MAX_ERROR_COUNT:
                    raise MaxTriesAPIError(self.MAX_ERROR_COUNT)

        target_file.close()

        task_args['input_file'] = target_file_name
        task_args['count'] = count

        return task_args
