import csv
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import SubscriberValues, Subscriber
from ivetl.pipelines.customsubscriberdata import CustomSubscriberDataPipeline
from ivetl.pipelines.subscriberdata import SubscribersAndSubscriptionsPipeline
from ivetl import utils


@app.task
class InsertCustomSubscriberDataIntoCassandraTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']
        total_count = task_args['count']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        for f in files:
            encoding = utils.guess_encoding(f)
            with open(f, encoding=encoding) as tsv:
                count = 0
                for line in csv.reader(tsv, delimiter='\t'):
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    # skip header row
                    if count == 1:
                        continue

                    membership_no = line[CustomSubscriberDataPipeline.FIELD_NAMES['membership_no']]
                    try:
                        subscriber = Subscriber.objects.get(publisher_id=publisher_id, membership_no=membership_no)
                    except Subscriber.DoesNotExist:
                        tlogger.info('Subscriber %s not found, skipping...' % membership_no)
                        continue

                    tlogger.info("Processing #%s : %s" % (count - 1, membership_no))

                    for attr_name in SubscribersAndSubscriptionsPipeline.CUSTOMIZABLE_FIELD_NAMES:
                        SubscriberValues.objects(
                            publisher_id=subscriber.publisher_id,
                            membership_no=membership_no,
                            source='custom',
                            name=attr_name,
                        ).update(
                            value_text=line[CustomSubscriberDataPipeline.FIELD_NAMES[attr_name]],
                        )

        task_args['count'] = total_count

        return task_args
