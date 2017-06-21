import csv
import datetime
from dateutil.parser import parse
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import InstitutionUsageStat, SystemGlobal


@app.task
class InsertJR3IntoCassandraTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']
        total_count = task_args['count']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        now = datetime.datetime.now()
        earliest_date = datetime.date(now.year, now.month, 1)

        count = 0
        for file in files:

            tlogger.info('Processing %s' % file)

            date_cols = []
            num_cols = 6
            with open(file, 'r', encoding='ISO-8859-1') as tsv:
                got_header_for_file = False

                for line in csv.reader(tsv, delimiter="\t"):
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    if not got_header_for_file:

                        # date cols start here
                        col = 6

                        # collect all of them (we support any number of them)
                        while line[col] != 'YTD Total':
                            month_date = parse(line[col])
                            full_date = datetime.date(month_date.year, month_date.month, 1)  # hard set to 1st of month
                            date_cols.append((col, full_date))
                            col += 1

                        num_cols += len(date_cols)

                        tlogger.info('Found %s date columns' % len(date_cols))
                        got_header_for_file = True
                        continue

                    if len(line) < num_cols:
                        tlogger.info('Unexpected number of cols, skipping row...')
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
                            continue

                        try:
                            stat = InstitutionUsageStat.objects.get(
                                publisher_id=publisher_id,
                                counter_type='jr3',
                                journal=journal,
                                subscriber_id=subscriber_id,
                                usage_date=date,
                                usage_category=usage_category,
                            )
                        except InstitutionUsageStat.DoesNotExist:
                            stat = InstitutionUsageStat.objects.create(
                                publisher_id=publisher_id,
                                counter_type='jr3',
                                journal=journal,
                                subscriber_id=subscriber_id,
                                usage_date=date,
                                usage_category=usage_category,
                            )

                        if usage != stat.usage:
                            stat.update(
                                journal_print_issn=journal_print_issn,
                                journal_online_issn=journal_online_issn,
                                institution_name=institution_name,
                                usage=usage,
                            )

                            if date < earliest_date:
                                earliest_date = datetime.date(date.year, date.month, 1)

        earliest_date_value_global_name = publisher_id + '_institution_usage_stat_earliest_date_value'
        earliest_date_updated_global_name = publisher_id + '_institution_usage_stat_earliest_date_updated'

        try:
            earliest_date_global = SystemGlobal.objects.get(name=earliest_date_value_global_name)
        except SystemGlobal.DoesNotExist:
            earliest_date_global = None

        if not earliest_date_global or earliest_date < earliest_date_global.date_value:
            SystemGlobal.objects(name=earliest_date_value_global_name).update(date_value=earliest_date)

        SystemGlobal.objects(name=earliest_date_updated_global_name).update(int_value=1)

        task_args['count'] = count
        return task_args
