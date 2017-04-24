import csv
import codecs
import json
from ivetl.celery import app
from ivetl.pipelines.task import Task


@app.task
class PrepareInputFileTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']
        total_count = task_args['count']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        target_file_name = work_folder + "/" + publisher_id + "_" + "preparedinput" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\t'
                          'MANUSCRIPT_ID\t'
                          'DATA\n')

        for file in files:
            with codecs.open(file, encoding="utf-8") as tsv:
                count = 0
                for line in csv.reader(tsv, delimiter="\t", quoting=csv.QUOTE_NONE):
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    # skip header row
                    if count == 1:
                        continue

                    tlogger.info("\n" + str(count-1) + ". Reading In Rejected Article: " + line[3])

                    input_data = {}
                    input_data['manuscript_id'] = line[0].strip()
                    input_data['date_of_rejection'] = line[1].strip()
                    input_data['reject_reason'] = line[2].strip()
                    input_data['title'] = line[3].strip()
                    input_data['first_author'] = line[4].strip()
                    input_data['corresponding_author'] = line[5].strip()
                    input_data['co_authors'] = line[6].strip()
                    input_data['subject_category'] = line[7].strip()
                    input_data['editor'] = line[8].strip()
                    input_data['submitted_journal'] = line[9].strip()

                    if len(line) >= 11 and line[10].strip() != '':
                        input_data['article_type'] = line[10].strip()

                    if len(line) >= 12 and line[11].strip() != '':
                        input_data['keywords'] = line[11].strip()

                    if len(line) >= 13 and line[12].strip() != '':
                        input_data['custom'] = line[12].strip()

                    if len(line) >= 14 and line[13].strip() != '':
                        input_data['funders'] = line[13].strip()

                    if len(line) >= 15 and line[14].strip() != '':
                        input_data['preprint_doi'] = line[14].strip()

                    input_data['source_file_name'] = file

                    row = """%s\t%s\t%s\n""" % (
                        publisher_id,
                        input_data['manuscript_id'],
                        json.dumps(input_data)
                    )

                    target_file.write(row)
                    target_file.flush()  # not sure why this is needed?

        target_file.close()

        task_args['count'] = count
        task_args['input_file'] = target_file_name
        return task_args
