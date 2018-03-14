import csv
import datetime
from decimal import Decimal
from dateutil.parser import parse
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import SubscriptionPricing, SystemGlobal
from ivetl import utils


@app.task
class InsertSubscriptionPricingIntoCassandraTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']
        total_count = task_args['count']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        earliest_year = datetime.datetime.now().year

        count = 0
        for file in files:

            tlogger.info('Processing %s' % file)

            encoding = utils.guess_encoding(file)
            with open(file, 'r', encoding=encoding) as tsv:
                for line in csv.reader(tsv, delimiter="\t"):

                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    # skip header row
                    if count == 1:
                        continue

                    membership_no = line[0]
                    year = int(line[1])
                    bundle_name = line[2]

                    if line[3]:
                        on_trial = True if line[3].upper() == 'Y' else False
                    else:
                        on_trial = None

                    if line[4]:
                        trial_expiration_date = parse(line[4])
                    else:
                        trial_expiration_date = None

                    amount = Decimal(line[5])

                    SubscriptionPricing.objects(
                        publisher_id=publisher_id,
                        membership_no=membership_no,
                        year=year,
                        bundle_name=bundle_name,
                    ).update(
                        trial=on_trial,
                        trial_expiration_date=trial_expiration_date,
                        amount=amount,
                    )

                    if year < earliest_year:
                        earliest_year = year

        # Note: we dirty two flags here: one for inst deltas and one for cost deltas

        earliest_date = datetime.datetime(earliest_year, 1, 1)

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
