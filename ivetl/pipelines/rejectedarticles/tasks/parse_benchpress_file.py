import os
import csv
import codecs
import json
from ivetl.celery import app
from ivetl.pipelines.task import Task


@app.task
class ParseBenchPressFileTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']

        # count all the lines in all the files
        total_count = 0
        for file in files:
            with codecs.open(file, encoding='utf-8') as f:
                for i, l in enumerate(f):
                    pass
                total_count = i + 1

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0

        target_file_name = work_folder + "/" + publisher_id + "_" + "preparedinput" + "_" + "target.tab"
        with codecs.open(target_file_name, 'w', 'utf-16') as target_file:
            target_file.write('PUBLISHER_ID\tMANUSCRIPT_ID\tDATA\n')

            for file in files:

                tlogger.info('Parsing file: %s' % file)

                with open(file, encoding='utf-8') as tsv:
                    reader = csv.DictReader(tsv, delimiter='\t', quoting=csv.QUOTE_NONE)
                    source_file_name = os.path.basename(file)
                    for row in reader:
                        count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                        # blood
                        # if '275073' not in row['MANUSCRIPT_ID']:
                        #     continue

                        # cob
                        # if '046896' not in row['MANUSCRIPT_ID']:
                        #     continue

                        # cob
                        # got_one = False
                        # for m in ['072678', '076752', '078675', '076141', '088013', '090597']:
                        #     if m in row['MANUSCRIPT_ID']:
                        #         got_one = True
                        #
                        # if not got_one:
                        #     continue

                        # if '074864' not in row['MANUSCRIPT_ID']:
                        #     continue

                        # the date in the BP file is d/m/y and the rest of the pipeline expects m/d/y
                        day, month, year = row['DATE_OF_REJECTION'].split('/')
                        fixed_date_of_rejection = '/'.join([month, day, year])

                        input_data = {
                            'manuscript_id': row['MANUSCRIPT_ID'],
                            'date_of_rejection': fixed_date_of_rejection,
                            'reject_reason': row['REJECT_REASON'],
                            'title': row['TITLE'].replace('"', ''),
                            'first_author': row['FIRST_AUTHOR'],
                            'corresponding_author': row['CORRESPONDING_AUTHOR'],
                            'co_authors': row['CO_AUTHORS'],
                            'subject_category': row['SUBJECT_CATEGORY'],
                            'editor': row['EDITOR'],
                            'submitted_journal': row['SUBMITTED_JOURNAL'],
                            'article_type': row['ARTICLE_TYPE'],
                            'keywords': row['KEYWORDS'],
                            'custom': row['CUSTOM'],
                            'funders': row['FUNDERS'],
                            'source_file_name': source_file_name,
                        }

                        row = """%s\t%s\t%s\n""" % (
                            publisher_id,
                            input_data['manuscript_id'],
                            json.dumps(input_data)
                        )

                        target_file.write(row)

        task_args['count'] = count
        task_args['input_file'] = target_file_name
        return task_args
