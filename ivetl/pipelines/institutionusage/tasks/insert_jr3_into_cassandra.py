import csv
import datetime
from dateutil.parser import parse
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import InstitutionUsageStat, InstitutionUsageStatComposite, InstitutionUsageJournal, SystemGlobal


@app.task
class InsertJR3IntoCassandraTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']
        total_count = task_args['count']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        now = datetime.datetime.now()
        earliest_date = datetime.datetime(now.year, now.month, 1)

        seen_journals = {j.journal for j in InstitutionUsageJournal.objects.filter(publisher_id=publisher_id, counter_type='jr3')}

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
                            full_date = datetime.datetime(month_date.year, month_date.month, 1)  # hard set to 1st of month
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

                    if journal not in seen_journals:
                        InstitutionUsageJournal.objects.create(
                            publisher_id=publisher_id,
                            counter_type='jr3',
                            journal=journal,
                        )
                        seen_journals.add(journal)

                    for col, date in date_cols:

                        try:
                            usage = int(line[col])
                        except ValueError:
                            continue

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

                        InstitutionUsageStatComposite.objects(
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

                        if date < earliest_date:
                            earliest_date = datetime.datetime(date.year, date.month, 1)

        # Note: we dirty two flags here: one for inst deltas and one for cost deltas

        earliest_date_for_inst_value_global_name = publisher_id + '_institution_usage_stat_earliest_date_value'
        earliest_date_for_inst_dirty_global_name = publisher_id + '_institution_usage_stat_earliest_date_dirty'

        try:
            earliest_date_for_inst_global = SystemGlobal.objects.get(name=earliest_date_for_inst_value_global_name)
        except SystemGlobal.DoesNotExist:
            earliest_date_for_inst_global = None

        if not earliest_date_for_inst_global or earliest_date < earliest_date_for_inst_global.date_value:
            SystemGlobal.objects(name=earliest_date_for_inst_value_global_name).update(date_value=earliest_date)

        SystemGlobal.objects(name=earliest_date_for_inst_dirty_global_name).update(int_value=1)

        earliest_date_for_cost_value_global_name = publisher_id + '_institution_usage_stat_for_cost_earliest_date_value'
        earliest_date_for_cost_dirty_global_name = publisher_id + '_institution_usage_stat_for_cost_earliest_date_dirty'

        try:
            earliest_date_for_cost_global = SystemGlobal.objects.get(name=earliest_date_for_cost_value_global_name)
        except SystemGlobal.DoesNotExist:
            earliest_date_for_cost_global = None

        if not earliest_date_for_cost_global or earliest_date < earliest_date_for_cost_global.date_value:
            SystemGlobal.objects(name=earliest_date_for_cost_value_global_name).update(date_value=earliest_date)

        SystemGlobal.objects(name=earliest_date_for_cost_dirty_global_name).update(int_value=1)

        task_args['count'] = count
        task_args['from_date'] = self.to_json_date(earliest_date)
        return task_args
