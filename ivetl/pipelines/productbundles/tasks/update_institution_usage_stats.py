from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import InstitutionUsageStat, SubscriptionPricing, ProductBundle


@app.task
class UpdateInstitutionUsageStatsTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        publisher_stats = InstitutionUsageStat.objects.filter(publisher_id=publisher_id, counter_type='jr3').limit(10000000)

        total_count = 100000  # cheap estimate
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0
        for stat in publisher_stats:
            count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

            # get subscriptions for this pub and year
            matching_subscriptions = SubscriptionPricing.objects.filter(
                publisher_id=publisher_id,
                membership_no=stat.subscriber_id,
                year=stat.usage_date.year,
            )

            tlogger.info('Matching stat: %s, %s, %s' % (stat.publisher_id, stat.counter_type, stat.journal))

            # find one with a matching ISSN
            match = None
            for subscription in matching_subscriptions:
                try:
                    bundle = ProductBundle.objects.get(
                        publisher_id=publisher_id,
                        bundle_name=subscription.bundle_name,
                    )

                    issns = bundle.journal_issns
                    if stat.journal_print_issn in issns or stat.journal_online_issn in issns:
                        match = subscription
                        break

                except ProductBundle.DoesNotExist:
                    pass

            if match:
                tlogger.info('Found match, updating with bundle info: %s' % match.bundle_name)
                stat.update(
                    bundle_name=match.bundle_name,
                    trial=match.trial,
                    trial_expiration_date=match.trial_expiration_date,
                    amount=match.amount,
                )
            else:
                tlogger.info('No match found')

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id)

        return {
            'count': count
        }
