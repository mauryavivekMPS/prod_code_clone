import csv
import codecs
import json
from ivetl.common import common
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.connectors import MendeleyConnector
from ivetl.alerts import run_alert


@app.task
class MendeleyLookupTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        file = task_args['input_file']
        total_count = task_args['count']

        target_file_name = work_folder + "/" + publisher_id + "_" + "mendeleylookup" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\tDOI\tISSN\tDATA\n')

        mendeley = MendeleyConnector(common.MENDELEY_CLIENT_ID, common.MENDELEY_CLIENT_SECRET)

        count = 0
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                if count == 1:
                    continue

                publisher_id = line[0]
                doi = line[1]
                issn = line[2]
                data = json.loads(line[3])

                tlogger.info(str(count-1) + ". Retrieving Mendelez saves for: " + doi)

                try:
                    new_saves_value = mendeley.get_saves(doi)
                    data['mendeley_saves'] = new_saves_value
                    run_alert(
                        check_id='mendeley-saves-exceeds-value',
                        publisher_id=publisher_id,
                        new_value=new_saves_value,
                    )
                except:
                    tlogger.info("General Exception - Mendelez API failed. Moving to next article...")

                row = """%s\t%s\t%s\t%s\n""" % (publisher_id, doi, issn, json.dumps(data))

                target_file.write(row)
                target_file.flush()

        target_file.close()

        task_args['input_file'] = target_file_name
        task_args['count'] = count

        return task_args
