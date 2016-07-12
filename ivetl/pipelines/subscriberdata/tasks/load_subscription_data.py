import csv
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import Subscriber
from ivetl import utils


@app.task
class LoadSubscriptionDataTask(Task):
    FILE_PATH = '/iv/hwdw-metadata/subscriptions.csv'

    FIELD_NAMES = [
        'etc',
    ]

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        total_count = utils.file_len(self.FILE_PATH)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)
        tlogger.info('Found %s records' % total_count)

        count = 0
        with open(self.FILE_PATH, encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t', fieldnames=self.FIELD_NAMES)
            for row in reader:
                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                # match publisher id
                publisher_id = 'foo'

                Subscriber.objects(
                    publisher_id=publisher_id,
                    membership_no=row['membership_no']
                ).update(
                    ac_database=row['ac_database'],
                )

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id)

        task_args['count'] = total_count

        return task_args
