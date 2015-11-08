import csv
import codecs
import json
from ivetl.celery import app
from ivetl.connectors.base import MaxTriesAPIError
from ivetl.connectors.scopus import ScopusConnector
from ivetl.models import Publisher_Metadata, Published_Article
from ivetl.pipelines.task import Task


@app.task
class ScopusIdLookupTask(Task):

    MAX_ERROR_COUNT = 100

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        file = task_args[self.INPUT_FILE]

        target_file_name = work_folder + "/" + publisher_id + "_" + "scopuscitationlookup" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\t'
                          'DOI\t'
                          'ISSN\t'
                          'DATA\n')

        pm = Publisher_Metadata.objects.filter(publisher_id=publisher_id).first()
        connector = ScopusConnector(pm.scopus_api_keys)

        count = 0
        error_count = 0

        total_count = 0
        with codecs.open(file, encoding="utf-16") as f:
            for i, l in enumerate(f):
                pass
            total_count = i + 1

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
                existing_record = Published_Article.objects.filter(publisher_id=publisher_id, article_doi=doi).first()

                if existing_record and existing_record.article_scopus_id is not None:
                    data['scopus_id_status'] = "DOI in Scopus"
                    data['scopus_id'] = existing_record.article_scopus_id
                    data['scopus_citation_count'] = existing_record.scopus_citation_count

                    tlogger.info("Scopus Id already retrieved in previous run")

                else:
                    try:
                        scopus_id, scopus_cited_by = connector.get_entry(doi, data.get('ISSN'),
                                                                              data.get('volume'),
                                                                              data.get('issue'),
                                                                              data.get('page'),
                                                                              tlogger)

                        if scopus_id is not None and scopus_cited_by is not None:

                            data['scopus_id_status'] = "DOI in Scopus"
                            data['scopus_id'] = scopus_id
                            data['scopus_citation_count'] = scopus_cited_by
                        else:

                            tlogger.info("No Scopus Id found for DOI: " + doi)
                            data['scopus_id_status'] = "No DOI in Scopus"
                            data['scopus_id'] = ''

                    except MaxTriesAPIError:
                        tlogger.info("Scopus API failed.")
                        data['scopus_id'] = ''
                        data['scopus_id_status'] = "Scopus API failed"
                        error_count += 1

                row = """%s\t%s\t%s\t%s\n""" % (publisher_id,
                                            doi,
                                            issn,
                                            json.dumps(data))

                target_file.write(row)
                target_file.flush()

                if error_count >= self.MAX_ERROR_COUNT:
                    raise MaxTriesAPIError(self.MAX_ERROR_COUNT)

            tsv.close()

        target_file.close()

        task_args[self.INPUT_FILE] = target_file_name
        task_args[self.COUNT] = count

        return task_args






