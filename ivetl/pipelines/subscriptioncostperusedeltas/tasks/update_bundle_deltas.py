import datetime
import decimal
from dateutil.relativedelta import relativedelta
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import SubscriptionCostPerUseByBundleStat, SubscriptionCostPerUseByBundleStatDelta
from ivetl import utils


@app.task
class UpdateBundleDeltasTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        from_date = self.from_json_date(task_args.get('from_date'))
        to_date = self.from_json_date(task_args.get('to_date'))

        total_count = utils.get_record_count_estimate(publisher_id, product_id, pipeline_id, self.short_name)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0

        stopped = False

        for current_month in utils.month_range(from_date, to_date):

            tlogger.info('Processing month %s' % current_month.strftime('%Y-%m'))
            tlogger.info(current_month)

            # select all usage for the current (iterated) month
            all_current_month_cost_per_use = SubscriptionCostPerUseByBundleStat.objects.filter(
                publisher_id=publisher_id,
                usage_date=current_month,
            ).fetch_size(1000).limit(10000000)

            for current_cost_per_use in all_current_month_cost_per_use:

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                # early stop support
                if count % 1000:
                    if self.is_stopped(publisher_id, product_id, pipeline_id, job_id):
                        self.mark_as_stopped(publisher_id, product_id, pipeline_id, job_id)
                        stopped = True
                        break

                #
                # time_slice == 'm' (month)
                #

                previous_month = current_month - relativedelta(months=1)

                try:
                    previous_cost_per_use = SubscriptionCostPerUseByBundleStat.objects.get(
                        publisher_id=publisher_id,
                        membership_no=current_cost_per_use.membership_no,
                        bundle_name=current_cost_per_use.bundle_name,
                        usage_date=previous_month,
                    )

                    absolute_delta = current_cost_per_use.cost_per_use - previous_cost_per_use.cost_per_use
                    if previous_cost_per_use.cost_per_use:
                        percentage_delta = absolute_delta / previous_cost_per_use.cost_per_use
                    else:
                        percentage_delta = 0.0

                    SubscriptionCostPerUseByBundleStatDelta.objects(
                        publisher_id=publisher_id,
                        membership_no=current_cost_per_use.membership_no,
                        bundle_name=current_cost_per_use.bundle_name,
                        usage_date=current_month,
                        time_slice='m',
                    ).update(
                        previous_amount=previous_cost_per_use.amount,
                        previous_total_usage=previous_cost_per_use.total_usage,
                        current_amount=current_cost_per_use.amount,
                        current_total_usage=current_cost_per_use.total_usage,
                        previous_cost_per_use=previous_cost_per_use.cost_per_use,
                        current_cost_per_use=current_cost_per_use.cost_per_use,
                        absolute_delta=absolute_delta,
                        percentage_delta=percentage_delta,
                    )

                except SubscriptionCostPerUseByBundleStat.DoesNotExist:
                    pass

                #
                # time_slice == 'ytd' (year-to-date)
                #

                start_of_previous_year = datetime.date(current_month.year - 1, 1, 1)
                current_month_previous_year = datetime.date(current_month.year - 1, current_month.month, 1)
                previous_ytd_total_usage = 0
                previous_ytd_amount = decimal.Decimal(0)
                previous_ytd_cost_per_use = decimal.Decimal(0)
                found_first_ytd_cost_per_use = True
                for m in utils.month_range(start_of_previous_year, current_month_previous_year):
                    try:
                        u = SubscriptionCostPerUseByBundleStat.objects.get(
                            publisher_id=publisher_id,
                            membership_no=current_cost_per_use.membership_no,
                            bundle_name=current_cost_per_use.bundle_name,
                            usage_date=m,
                        )
                        if u.total_usage:
                            previous_ytd_total_usage += u.total_usage
                        if u.amount:
                            previous_ytd_amount += u.amount
                        if m == start_of_previous_year:
                            found_first_ytd_cost_per_use = True
                    except SubscriptionCostPerUseByBundleStat.DoesNotExist:
                        if not found_first_ytd_cost_per_use:
                            break

                if found_first_ytd_cost_per_use:
                    start_of_current_year = datetime.date(current_month.year, 1, 1)
                    current_ytd_total_usage = 0
                    current_ytd_amount = decimal.Decimal(0)
                    current_ytd_cost_per_use = decimal.Decimal(0)
                    for m in utils.month_range(start_of_current_year, current_month):
                        try:
                            u = SubscriptionCostPerUseByBundleStat.objects.get(
                                publisher_id=publisher_id,
                                membership_no=current_cost_per_use.membership_no,
                                bundle_name=current_cost_per_use.bundle_name,
                                usage_date=m,
                            )
                            if u.total_usage:
                                current_ytd_total_usage += u.total_usage
                            if u.amount:
                                current_ytd_amount += u.amount
                        except SubscriptionCostPerUseByBundleStat.DoesNotExist:
                            pass

                    if previous_ytd_total_usage:
                        previous_ytd_cost_per_use = previous_ytd_amount / previous_ytd_total_usage

                    if current_ytd_total_usage:
                        current_ytd_cost_per_use = current_ytd_amount / current_ytd_total_usage

                    absolute_ytd_delta = current_ytd_cost_per_use - previous_ytd_cost_per_use
                    if previous_ytd_cost_per_use:
                        percentage_ytd_delta = absolute_ytd_delta / previous_ytd_cost_per_use
                    else:
                        percentage_ytd_delta = 0.0

                    SubscriptionCostPerUseByBundleStatDelta.objects(
                        publisher_id=publisher_id,
                        membership_no=current_cost_per_use.membership_no,
                        bundle_name=current_cost_per_use.bundle_name,
                        usage_date=current_month,
                        time_slice='ytd',
                    ).update(
                        previous_amount=previous_ytd_amount,
                        previous_total_usage=previous_ytd_total_usage,
                        current_amount=current_ytd_amount,
                        current_total_usage=current_ytd_total_usage,
                        previous_cost_per_use=previous_ytd_cost_per_use,
                        current_cost_per_use=current_ytd_cost_per_use,
                        absolute_delta=absolute_ytd_delta,
                        percentage_delta=percentage_ytd_delta,
                    )

            if stopped:
                break

        task_args['count'] = count
        return task_args
