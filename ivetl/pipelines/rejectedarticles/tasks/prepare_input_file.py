import csv
import codecs
import json
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.utils import trim_and_strip_doublequotes


@app.task
class PrepareInputFileTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']
        total_count = task_args['count']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        target_file_name = work_folder + "/" + publisher_id + "_" + "preparedinput" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('\t'.join(['PUBLISHER_ID', 'MANUSCRIPT_ID', 'DATA']) + '\n')

        count = 0

        for file in files:
            with codecs.open(file, encoding="utf-8") as tsv:
                count_in_file = 0

                for line in csv.reader(tsv, delimiter="\t", quoting=csv.QUOTE_NONE):
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                    count_in_file += 1

                    # skip header row
                    if count_in_file == 1:
                        continue

                    tlogger.info("\n" + str(count-1) + ". Reading In Rejected Article: " + line[3])

                    manuscript_id = trim_and_strip_doublequotes(line[0])
                    input_data = {
                        'manuscript_id': manuscript_id,
                        'date_of_rejection': trim_and_strip_doublequotes(line[1]),
                        'reject_reason': trim_and_strip_doublequotes(line[2]),
                        'title': trim_and_strip_doublequotes(line[3]),
                        'first_author': trim_and_strip_doublequotes(line[4]),
                        'corresponding_author': trim_and_strip_doublequotes(line[5]),
                        'co_authors': trim_and_strip_doublequotes(line[6]),
                        'subject_category': trim_and_strip_doublequotes(line[7]),
                        'editor': trim_and_strip_doublequotes(line[8]),
                        'submitted_journal': trim_and_strip_doublequotes(line[9]),
                    }

                    if len(line) >= 11:
                        article_type = trim_and_strip_doublequotes(line[10])
                        if article_type:
                            input_data['article_type'] = article_type

                    if len(line) >= 12:
                        keywords = trim_and_strip_doublequotes(line[11])
                        if keywords:
                            input_data['keywords'] = keywords

                    if len(line) >= 13:
                        custom = trim_and_strip_doublequotes(line[12])
                        if custom:
                            input_data['custom'] = custom

                    if len(line) >= 14:
                        funders = trim_and_strip_doublequotes(line[13])
                        if funders:
                            input_data['funders'] = funders

                    if len(line) >= 15:
                        preprint_doi = trim_and_strip_doublequotes(line[14])
                        if preprint_doi:
                            input_data['preprint_doi'] = preprint_doi

                    input_data['source_file_name'] = file

                    row = '\t'.join([publisher_id, manuscript_id, json.dumps(input_data)]) + '\n'
                    target_file.write(row)

        target_file.close()

        task_args['count'] = count
        task_args['input_file'] = target_file_name
        return task_args
