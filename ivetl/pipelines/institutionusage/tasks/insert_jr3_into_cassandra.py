import csv
from dateutil.parser import parse
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import InstitutionUsageStat


@app.task
class InsertJR3IntoCassandra(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']
        total_count = task_args['count']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0
        for file in files:

            tlogger.info('Processing %s' % file)

            date_cols = []
            with open(file, 'r', encoding='windows-1252') as tsv:
                for line in csv.reader(tsv, delimiter="\t"):

                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                    if count == 1:

                        # date cols start here
                        col = 6

                        # collect all of them (we support any number of them)
                        while line[col] != 'YTD Total':
                            date = parse(line[col])
                            date_cols.append((col, date))
                            col += 1

                        tlogger.info('Found %s date columns' % len(date_cols))
                        continue

                    subscriber_id = line[0]
                    institution_name = line[1]
                    journal = line[2]
                    journal_print_issn = line[3]
                    journal_online_issn = line[4]
                    usage_category = line[5]

                    for col, date in date_cols:

                        try:
                            usage = int(line[col])
                        except ValueError:
                            usage = 0

                        InstitutionUsageStat.objects(
                            publisher_id=publisher_id,
                            counter_type='jr3',
                            journal=journal,
                            subscriber_id=subscriber_id,
                            usage_date=date,
                            usage_category=usage_category,
                        ).update(
                            journal_print_issn=journal_print_issn,
                            journal_online_issn=journal_online_issn,
                            institution_name=institution_name,
                            usage=usage,
                        )

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id)

        return {
            'count': count
        }