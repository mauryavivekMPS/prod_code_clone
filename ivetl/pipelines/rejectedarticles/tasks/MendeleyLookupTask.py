import csv
import codecs
import json
from ivetl.common import common
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.connectors import MendeleyConnector


@app.task
class MendeleyLookupTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        file = task_args['input_file']
        total_count = task_args['count']

        target_file_name = work_folder + "/" + publisher_id + "_" + "mendeleylookup" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\tMANUSCRIPT_ID\tDATA\n')

        mendeley = MendeleyConnector(common.MENDELEY_CLIENT_ID, common.MENDELEY_CLIENT_SECRET)

        count = 0
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                if count == 1:
                    continue

                publisher_id = line[0]
                manuscript_id = line[1]
                data = json.loads(line[2])

                if data['status'] == "Match found":

                    tlogger.info(str(count-1) + ". Retrieving Mendeley saves for: " + doi)

                    doi = data['xref_doi']

                    try:
                        data['mendeley_saves'] = mendeley.get_saves(doi)
                    except:
                        tlogger.info("No Saves. Moving to next article...")
                else:
                    tlogger.info(str(count-1) + ". No match found for manuscript, skipping retrieval of Mendeley saves for: " + doi)

                row = """%s\t%s\t%s\n""" % (publisher_id, manuscript_id, json.dumps(data))

                target_file.write(row)

        target_file.close()

        return {
            'input_file': target_file_name,
            'count': count,
        }
