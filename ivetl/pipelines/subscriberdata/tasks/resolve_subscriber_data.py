from dateutil.parser import parse
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import Subscriber, SubscriberValues, PublisherMetadata
from ivetl.pipelines.subscriberdata import SubscribersAndSubscriptionsPipeline
from ivetl.pipelines.subscriberdata.tasks import LoadSubscriberDataTask
from ivetl.common import common


@app.task
class ResolveSubscriberDataTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        pipeline = common.PIPELINE_BY_ID['subscribers_and_subscriptions']

        if publisher_id == pipeline['single_publisher_id']:
            publisher_id_list = [p.publisher_id for p in PublisherMetadata.objects.all() if getattr(p, pipeline['update_publisher_datasource_if_attr_is_true'])]
        else:
            publisher_id_list = [publisher_id]

        overlapping_fields = set(LoadSubscriberDataTask.FIELD_NAMES).intersection(set(SubscribersAndSubscriptionsPipeline.CUSTOMIZABLE_FIELD_NAMES))

        total_count = len(publisher_id_list) * 3000  # just have to use a guess
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0

        for subscriber_publisher_id in publisher_id_list:
            tlogger.info('Processing publisher: %s' % subscriber_publisher_id)

            all_inst_subscribers = Subscriber.objects.filter(publisher_id=subscriber_publisher_id, user_type='INST').fetch_size(1000).limit(10000000)

            for subscriber in all_inst_subscribers:
                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                # resolve policy: if a value from source=custom is present it always wins
                for attr_name in SubscribersAndSubscriptionsPipeline.CUSTOMIZABLE_FIELD_NAMES:
                    new_value = None
                    try:
                        v = SubscriberValues.objects.get(
                            publisher_id=subscriber.publisher_id,
                            membership_no=subscriber.membership_no,
                            source='custom',
                            name=attr_name
                        )
                        new_value = v.value_text
                    except SubscriberValues.DoesNotExist:
                        pass

                    if not new_value and attr_name in overlapping_fields:
                        try:
                            v = SubscriberValues.objects.get(
                                publisher_id=subscriber.publisher_id,
                                membership_no=subscriber.membership_no,
                                source='hw',
                                name=attr_name
                            )
                            new_value = v.value_text
                        except SubscriberValues.DoesNotExist:
                            pass

                    # hard default to "None"
                    if not new_value:
                        new_value = "None"

                    # we hard default to "None", so always update
                    if attr_name in SubscribersAndSubscriptionsPipeline.CUSTOMIZABLE_DATETIME_FIELD_NAMES:
                        try:
                            new_value = parse(new_value)
                        except ValueError:
                            continue

                    setattr(subscriber, attr_name, new_value)

                subscriber.save()

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, tlogger, show_alerts=task_args['show_alerts'])

        task_args['count'] = count
        return task_args
