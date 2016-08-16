from dateutil.parser import parse
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import Subscriber, SubscriberValues, PublisherMetadata
from ivetl.pipelines.subscriberdata import SubscribersAndSubscriptionsPipeline
from ivetl.common import common


@app.task
class ResolveSubscriberDataTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        if publisher_id == common.PIPELINE_BY_ID['subscribers_and_subscriptions']['single_publisher_id']:
            publisher_id_list = [p.publisher_id for p in PublisherMetadata.objects.all() if p.ac_databases]
        else:
            publisher_id_list = [publisher_id]

        total_count = 1000000  # just have to use a guess
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0

        for subscriber_publisher_id in publisher_id_list:
            tlogger.info('Processing publisher: %s' % subscriber_publisher_id)

            all_subscribers = Subscriber.objects.filter(publisher_id=subscriber_publisher_id).limit(10000000)

            for subscriber in all_subscribers:
                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                # resolve policy: if a value from source=custom is present it always wins
                for attr_name, col_name in SubscribersAndSubscriptionsPipeline.OVERLAPPING_FIELDS:
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

                    if not new_value:
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

                    # update the canonical if there is any non Null/None value (note that "None" is a value)
                    if new_value:
                        if attr_name in SubscribersAndSubscriptionsPipeline.OVERLAPPING_DATETIMES:
                            try:
                                new_value = parse(new_value)
                            except ValueError:
                                continue

                        setattr(subscriber, attr_name, new_value)

                subscriber.save()

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id)

        task_args['count'] = count
        return task_args
