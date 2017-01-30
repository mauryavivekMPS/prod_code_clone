import csv
import codecs
import json
import traceback
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.connectors.base import MaxTriesAPIError
from ivetl.connectors.scopus import ScopusConnector
from ivetl.models import PublisherMetadata


@app.task
class ScopusCitationLookupTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        file = task_args['input_file']
        total_count = task_args['count']

        target_file_name = work_folder + "/" + publisher_id + "_" + "scopuscitationlookup" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\tMANUSCRIPT_ID\tDATA\n')

        count = 0
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        pm = PublisherMetadata.objects.filter(publisher_id=publisher_id).first()
        connector = ScopusConnector(pm.scopus_api_keys)

        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):
                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                if count == 1:
                    continue  # ignore the header

                publisher = line[0]
                manuscript_id = line[1]
                data = json.loads(line[2])

                tlogger.info("\n" + str(count-1) + ". Retrieving Citations for: " + manuscript_id)

                if data['status'] == "Match found":

                    doi = data['xref_doi']

                    try:
                        scopus_id, scopus_cited_by, subtype = connector.get_entry(doi, tlogger)

                    except MaxTriesAPIError:
                        tlogger.info("Scopus API failed. Trying Again")
                        traceback.print_exc()
                        data['citation_lookup_status'] = "Scopus API failed"
                        data['scopus_id'] = ''
                        data['scopus_doi_status'] = "Scopus API failed"

                    if scopus_id:
                        data['citation_lookup_status'] = "ID in Scopus"
                        data['scopus_doi_status'] = "DOI in Scopus"
                        data['scopus_id'] = scopus_id
                        data['citations'] = scopus_cited_by

                        tlogger.info("Scopus Cites = %s" % scopus_cited_by)
                    else:
                        tlogger.info("No Scopus Id found for DOI: " + data['xref_doi'])
                        data['scopus_doi_status'] = "No DOI in Scopus"
                        data['citation_lookup_status'] = "No ID in Scopus"
                        data['scopus_id'] = ''

                    tlogger.info(data['status'])

                row = "%s\t%s\t%s\n" % (publisher, manuscript_id, json.dumps(data))

                target_file.write(row)

        target_file.close()

        task_args['count'] = count
        task_args['input_file'] = target_file_name
        return task_args
