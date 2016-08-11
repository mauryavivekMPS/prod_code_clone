import datetime
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import InstitutionUsageStat, SubscriptionCostPerUseByBundleStat, SubscriptionCostPerUseBySubscriberStat
from ivetl import utils


@app.task
class UpdateCostPerUseTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        now = datetime.datetime.now()
        from_date = datetime.date(2013, 1, 1)
        to_date = datetime.date(now.year, now.month, 1)

        categories = {
            'Full-text HTML Requests': 'html_usage',
            'Full-text PDF Requests': 'pdf_usage',
        }

        count = 0

        for current_month in utils.month_range(from_date, to_date):

            tlogger.info('Processing month %s' % current_month.strftime('%Y-%m'))

            # select all html usage for the current (iterated) month
            current_month_usage = InstitutionUsageStat.objects.filter(
                publisher_id=publisher_id,
                counter_type='jr3',
                usage_date=current_month,
            )

            tlogger.info('Found %s total usage records' % current_month_usage.count())

            # first, fill out cpu by bundle
            for usage in current_month_usage:
                if usage.usage_category in categories and usage.bundle_name:
                    try:
                        s = SubscriptionCostPerUseByBundleStat.objects.get(
                            publisher_id=publisher_id,
                            membership_no=usage.subscriber_id,
                            bundle_name=usage.bundle_name,
                            usage_date=current_month,
                        )
                    except SubscriptionCostPerUseByBundleStat.DoesNotExist:
                        s = SubscriptionCostPerUseByBundleStat.objects.create(
                            publisher_id=publisher_id,
                            membership_no=usage.subscriber_id,
                            bundle_name=usage.bundle_name,
                            usage_date=current_month,
                            amount=usage.amount / 12,
                        )

                    s.category_usage[categories[usage.usage_category]] = usage.usage

                    total_usage = 0
                    for category_usage in s.category_usage.values():
                        total_usage += category_usage

                    if total_usage:
                        s.total_usage = total_usage
                        s.cost_per_use = s.amount / total_usage

                    # we calculate totals and cost_per_use incrementally
                    s.save()

            # and then use the new records to calculate across bundles


        return {
            'count': count
        }
