import csv
import codecs
import json
from ivetl.celery import app
from ivetl.pipelines.task import Task


@app.task
class PrepareForDBInsertTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        file = task_args['input_file']
        total_count = task_args['count']

        target_file_name = work_folder + "/" + publisher_id + "_" + "scopuscitationlookup" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\t'
                          'MANUSCRIPT_ID\t'
                          'DATA\n')

        count = 0
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):
                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                if count == 1:
                    continue  # ignore the header

                publisher = line[0]
                manuscript_id = line[1]
                data = json.loads(line[2])

                tlogger.info("\n" + str(count-1) + ". Preparing record: " + publisher + " / " + manuscript_id)

                if data['status'] == "No match found":
                    data['status'] = "Not Published"

                if data['status'] == "Match found" and data['citation_lookup_status'] == "ID in Scopus" and data['citations'] == "0":
                    data['status'] = "Published & Not Cited"

                if data['status'] == "Match found" and data['citation_lookup_status'] == "No ID in Scopus":
                    data['status'] = "Published & Citation Info Unavailable"

                if data['status'] == "Match found" and data['citation_lookup_status'] == "ID in Scopus" and data['citations'] != "0":
                    data['status'] = "Published & Cited"

                row = """%s\t%s\t%s\n""" % (publisher,
                                            manuscript_id,
                                            json.dumps(data))

                target_file.write(row)
                target_file.flush()

        target_file.close()

        task_args['count'] = count
        task_args['input_file'] = target_file_name
        return task_args
