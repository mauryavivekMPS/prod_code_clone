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

        stopped = False

        for current_month in utils.month_range(from_date, to_date):

            tlogger.info('Processing month %s' % current_month.strftime('%Y-%m'))

            # select all html usage for the current (iterated) month
            current_month_usage = InstitutionUsageStat.objects.filter(
                publisher_id=publisher_id,
                counter_type='jr3',
                usage_date=current_month,
            ).fetch_size(1000).limit(10000000)

            # first, fill out cpu by bundle
            for usage in current_month_usage:

                # early stop support
                if count % 1000:
                    if self.is_stopped(publisher_id, product_id, pipeline_id, job_id):
                        self.mark_as_stopped(publisher_id, product_id, pipeline_id, job_id)
                        stopped = True
                        break

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

                    s.total_usage = total_usage

                    if s.amount is not None and total_usage:
                        s.cost_per_use = s.amount / total_usage

                    s.save()

            # second, iterate over the just-created bundle stats
            current_month_bundle_stats = SubscriptionCostPerUseByBundleStat.objects.filter(
                publisher_id=publisher_id,
                usage_date=current_month,
            )

            if stopped:
                break

            for bundle_stat in current_month_bundle_stats:

                # early stop support
                if count % 1000:
                    if self.is_stopped(publisher_id, product_id, pipeline_id, job_id):
                        self.mark_as_stopped(publisher_id, product_id, pipeline_id, job_id)
                        stopped = True
                        break

                try:
                    s = SubscriptionCostPerUseBySubscriberStat.objects.get(
                        publisher_id=publisher_id,
                        membership_no=bundle_stat.membership_no,
                        usage_date=current_month,
                    )
                except SubscriptionCostPerUseBySubscriberStat.DoesNotExist:
                    s = SubscriptionCostPerUseBySubscriberStat.objects.create(
                        publisher_id=publisher_id,
                        membership_no=bundle_stat.membership_no,
                        usage_date=current_month,
                    )

                s.bundle_amount[bundle_stat.bundle_name] = bundle_stat.amount
                s.bundle_usage[bundle_stat.bundle_name] = bundle_stat.total_usage

                total_amount = 0
                for bundle_amount in s.bundle_amount.values():
                    total_amount += bundle_amount

                total_usage = 0
                for bundle_usage in s.bundle_usage.values():
                    total_usage += bundle_usage

                s.total_amount = total_amount
                s.total_usage = total_usage

                if total_amount is not None and total_usage:
                    s.cost_per_use = total_amount / total_usage

                s.save()

            if stopped:
                break

        task_args['count'] = count
        return task_args
