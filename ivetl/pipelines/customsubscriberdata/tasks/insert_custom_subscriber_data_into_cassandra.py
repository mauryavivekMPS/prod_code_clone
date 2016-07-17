import csv
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import SubscriberValues, Subscriber
from ivetl.pipelines.subscriberdata import SubscribersAndSubscriptionsPipeline


@app.task
class InsertCustomSubscriberDataIntoCassandraTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']
        total_count = task_args['count']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        for f in files:
            with open(f, encoding='utf-8') as tsv:
                count = 0
                for line in csv.DictReader(tsv, delimiter='\t'):
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    # skip header row
                    if count == 1:
                        continue

                    membership_no = line['membership_no']
                    subscriber = Subscriber.objects.get(membership_no=membership_no)
                    tlogger.info("Processing #%s : %s" % (count - 1, membership_no))

                    for field in SubscribersAndSubscriptionsPipeline.OVERLAPPING_FIELDS:
                        SubscriberValues.objects(
                            publisher_id=subscriber.publisher_id,
                            membership_no=membership_no,
                            source='custom',
                            name=field,
                        ).update(
                            value_text=line[field],
                        )

        task_args['count'] = total_count

        return task_args