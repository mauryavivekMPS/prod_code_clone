from dateutil.parser import parse
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import Subscriber, SubscriberValues
from ivetl.pipelines.subscriberdata import SubscribersAndSubscriptionsPipeline


@app.task
class ResolveSubscriberDataTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        all_subscribers = Subscriber.objects.all()

        total_count = all_subscribers.count()
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0
        for subscriber in all_subscribers:
            count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

            # resolve policy: if a value from source=custom is present it always wins
            for field in SubscribersAndSubscriptionsPipeline.OVERLAPPING_FIELDS:
                new_value = None
                try:
                    v = SubscriberValues.objects.get(
                        publisher_id=subscriber.publisher_id,
                        membership_no=subscriber.membership_no,
                        source='custom',
                        name=field
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
                            name=field
                        )
                        new_value = v.value_text
                    except SubscriberValues.DoesNotExist:
                        pass

                # update the canonical if there is any non Null/None value (note that "None" is a value)
                if new_value:
                    if field in SubscribersAndSubscriptionsPipeline.OVERLAPPING_DATETIMES:
                        try:
                            new_value = parse(new_value)
                        except ValueError:
                            continue

                    setattr(subscriber, field, new_value)

            subscriber.save()

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id)

        task_args['count'] = count
        return task_args
