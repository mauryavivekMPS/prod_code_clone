import datetime
from dateutil.relativedelta import relativedelta
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import SubscriptionCostPerUseBySubscriberStat, SubscriptionCostPerUseBySubscriberStatDelta
from ivetl import utils


@app.task
class UpdateSubscriberDeltasTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        now = datetime.datetime.now()
        from_date = datetime.date(2013, 1, 1)
        to_date = datetime.date(now.year, now.month, 1)

        total_count = None
        count = 0

        for current_month in utils.month_range(from_date, to_date):

            tlogger.info('Processing month %s' % current_month.strftime('%Y-%m'))
            tlogger.info(current_month)

            # select all usage for the current (iterated) month
            all_current_month_cost_per_use = SubscriptionCostPerUseBySubscriberStat.objects.filter(
                publisher_id=publisher_id,
                usage_date=current_month,
            ).limit(10000000)

            all_current_month_cost_per_use_count = all_current_month_cost_per_use.count()

            if all_current_month_cost_per_use_count:

                tlogger.info('Found %s records' % all_current_month_cost_per_use_count)

                # estimate the total count
                if total_count is None:
                    r = relativedelta(to_date, current_month)
                    months_remaining = r.years * 12 + r.months + 1
                    total_count = all_current_month_cost_per_use_count * months_remaining
                    self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

                for current_cost_per_use in all_current_month_cost_per_use:

                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    #
                    # time_slice == 'm' (month)
                    #

                    previous_month = current_month - relativedelta(months=1)

                    try:
                        previous_cost_per_use = SubscriptionCostPerUseBySubscriberStat.objects.get(
                            publisher_id=publisher_id,
                            membership_no=current_cost_per_use.membership_no,
                            usage_date=previous_month,
                        )

                        absolute_delta = current_cost_per_use.cost_per_use - previous_cost_per_use.cost_per_use
                        if previous_cost_per_use.cost_per_use:
                            percentage_delta = absolute_delta / previous_cost_per_use.cost_per_use
                        else:
                            percentage_delta = 0.0

                        SubscriptionCostPerUseBySubscriberStatDelta.objects(
                            publisher_id=publisher_id,
                            membership_no=current_cost_per_use.membership_no,
                            usage_date=current_month,
                            time_slice='m',
                        ).update(
                            previous_total_amount=previous_cost_per_use.total_amount,
                            previous_total_usage=previous_cost_per_use.total_usage,
                            current_total_amount=current_cost_per_use.total_amount,
                            current_total_usage=current_cost_per_use.total_usage,
                            previous_cost_per_use=previous_cost_per_use.cost_per_use,
                            current_cost_per_use=current_cost_per_use.cost_per_use,
                            absolute_delta=absolute_delta,
                            percentage_delta=percentage_delta,
                        )

                    except SubscriptionCostPerUseBySubscriberStat.DoesNotExist:
                        pass

                    #
                    # time_slice == 'ytd' (year-to-date)
                    #

                    start_of_previous_year = datetime.date(current_month.year - 1, 1, 1)
                    current_month_previous_year = datetime.date(current_month.year - 1, current_month.month, 1)
                    previous_ytd_total_usage = 0
                    previous_ytd_total_amount = 0
                    previous_ytd_cost_per_use = 0
                    found_first_ytd_cost_per_use = True
                    for m in utils.month_range(start_of_previous_year, current_month_previous_year):
                        try:
                            u = SubscriptionCostPerUseBySubscriberStat.objects.get(
                                publisher_id=publisher_id,
                                membership_no=current_cost_per_use.membership_no,
                                usage_date=m,
                            )
                            previous_ytd_total_usage += u.total_usage
                            previous_ytd_total_amount += u.total_amount
                            if m == start_of_previous_year:
                                found_first_ytd_cost_per_use = True
                        except SubscriptionCostPerUseBySubscriberStat.DoesNotExist:
                            if not found_first_ytd_cost_per_use:
                                break

                    if found_first_ytd_cost_per_use:
                        start_of_current_year = datetime.date(current_month.year, 1, 1)
                        current_ytd_total_usage = 0
                        current_ytd_total_amount = 0
                        current_ytd_cost_per_use = 0
                        for m in utils.month_range(start_of_current_year, current_month):
                            try:
                                u = SubscriptionCostPerUseBySubscriberStat.objects.get(
                                    publisher_id=publisher_id,
                                    membership_no=current_cost_per_use.membership_no,
                                    usage_date=m,
                                )
                                current_ytd_total_usage += u.total_usage
                                current_ytd_total_amount += u.total_amount
                            except SubscriptionCostPerUseBySubscriberStat.DoesNotExist:
                                pass

                        if previous_ytd_total_usage:
                            previous_ytd_cost_per_use = previous_ytd_total_amount / previous_ytd_total_usage

                        if current_ytd_total_usage:
                            current_ytd_cost_per_use = current_ytd_total_amount / current_ytd_total_usage

                        absolute_ytd_delta = current_ytd_cost_per_use - previous_ytd_cost_per_use
                        if previous_ytd_cost_per_use:
                            percentage_ytd_delta = absolute_ytd_delta / previous_ytd_cost_per_use
                        else:
                            percentage_ytd_delta = 0.0

                        SubscriptionCostPerUseBySubscriberStatDelta.objects(
                            publisher_id=publisher_id,
                            membership_no=current_cost_per_use.membership_no,
                            usage_date=current_month,
                            time_slice='ytd',
                        ).update(
                            previous_total_amount=previous_ytd_total_amount,
                            previous_total_usage=previous_ytd_total_usage,
                            current_total_amount=current_ytd_total_amount,
                            current_total_usage=current_ytd_total_usage,
                            previous_cost_per_use=previous_ytd_cost_per_use,
                            current_cost_per_use=current_ytd_cost_per_use,
                            absolute_delta=absolute_ytd_delta,
                            percentage_delta=percentage_ytd_delta,
                        )

            else:
                tlogger.info('No stats found')

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id)

        return {
            'count': count
        }
