import csv
from decimal import Decimal
from dateutil.parser import parse
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import SubscriptionPricing


@app.task
class InsertSubscriptionPricingIntoCassandraTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']
        total_count = task_args['count']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0
        for file in files:

            tlogger.info('Processing %s' % file)

            with open(file, 'r', encoding='utf-8') as tsv:
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

        task_args['count'] = count
        return task_args
