import csv
import codecs
import json
from ivetl.celery import app
from ivetl.connectors.base import MaxTriesAPIError
from ivetl.connectors.scopus import ScopusConnector
from ivetl.models import Publisher_Metadata, PublishedArticle
from ivetl.pipelines.task import Task


@app.task
class ScopusIdLookupTask(Task):
    MAX_ERROR_COUNT = 100

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        file = task_args['input_file']
        total_count = task_args['count']

        target_file_name = work_folder + "/" + publisher_id + "_" + "scopuscitationlookup" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\tDOI\tISSN\tDATA\n')

        pm = Publisher_Metadata.objects.filter(publisher_id=publisher_id).first()
        connector = ScopusConnector(pm.scopus_api_keys)

        count = 0
        error_count = 0
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):
                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                if count == 1:
                    continue  # ignore the header

                publisher_id = line[0]
                doi = line[1]
                issn = line[2]
                data = json.loads(line[3])

                tlogger.info("---")
                tlogger.info(str(count-1) + ". Retrieving Scopus Id for: " + doi)

                # If its already in the database, we don't have to check with scopus
                existing_record = PublishedArticle.objects.filter(publisher_id=publisher_id, article_doi=doi).first()

                if existing_record and existing_record.article_scopus_id and existing_record.scopus_subtype:
                    data['scopus_id_status'] = "DOI in Scopus"
                    data['scopus_id'] = existing_record.article_scopus_id
                    data['scopus_citation_count'] = existing_record.scopus_citation_count
                    data['scopus_subtype'] = existing_record.scopus_subtype
                    tlogger.info("Scopus Id already retrieved in previous run")

                else:
                    try:
                        scopus_id, scopus_cited_by, scopus_subtype = connector.get_entry(
                            doi,
                            tlogger,
                            data.get('ISSN'),
                            data.get('volume'),
                            data.get('issue'),
                            data.get('page')
                        )

                        if scopus_id and scopus_cited_by is not None:
                            data['scopus_id_status'] = "DOI in Scopus"
                            data['scopus_id'] = scopus_id
                            data['scopus_citation_count'] = scopus_cited_by
                            data['scopus_subtype'] = scopus_subtype
                        else:
                            tlogger.info("No Scopus Id found for DOI: " + doi)
                            data['scopus_id_status'] = "No DOI in Scopus"
                            data['scopus_id'] = ''

                    except MaxTriesAPIError:
                        tlogger.info("Scopus API failed.")
                        data['scopus_id'] = ''
                        data['scopus_id_status'] = "Scopus API failed"
                        error_count += 1

                row = "%s\t%s\t%s\t%s\n" % (publisher_id, doi, issn, json.dumps(data))

                target_file.write(row)
                target_file.flush()

                if error_count >= self.MAX_ERROR_COUNT:
                    raise MaxTriesAPIError(self.MAX_ERROR_COUNT)

        target_file.close()

        task_args['input_file'] = target_file_name
        task_args['count'] = count

        return task_args
