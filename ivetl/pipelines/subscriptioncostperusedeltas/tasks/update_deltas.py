import datetime
from dateutil.relativedelta import relativedelta
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import SubscriptionCostPerUseStat, SubscriptionCostPerUseStatDelta
from ivetl import utils


@app.task
class UpdateDeltasTask(Task):

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
            all_current_month_cost_per_use = SubscriptionCostPerUseStat.objects.filter(
                publisher_id=publisher_id,
                usage_date=current_month,
            )

            all_current_month_cost_per_use_count = all_current_month_cost_per_use.count()

            if all_current_month_cost_per_use_count:

                tlogger.info('Found %s records' % all_current_month_cost_per_use_count)

                # estimate the total count
                if total_count is None:
                    months_remaining = relativedelta(to_date, current_month).months + 1
                    total_count = all_current_month_cost_per_use_count * months_remaining
                    self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

                for current_cost_per_use in all_current_month_cost_per_use:

                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    #
                    # time_slice == 'm' (month)
                    #

                    previous_month = current_month - relativedelta(months=1)

                    try:
                        previous_cost_per_use = SubscriptionCostPerUseStat.objects.get(
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

                        SubscriptionCostPerUseStatDelta.objects(
                            publisher_id=publisher_id,
                            membership_no=current_cost_per_use.membership_no,
                            bundle_name=current_cost_per_use.bundle_name,
                            usage_date=current_month,
                            time_slice='m',
                        ).update(
                            previous_cost_per_use=previous_cost_per_use.cost_per_use,
                            current_cost_per_use=current_cost_per_use.cost_per_use,
                            absolute_delta=absolute_delta,
                            percentage_delta=percentage_delta,
                        )

                    except SubscriptionCostPerUseStat.DoesNotExist:
                        pass

                    #
                    # time_slice == 'qtd' (quarter-to-date)
                    #

                    start_of_previous_quarter = utils.start_of_previous_quarter(current_month)
                    current_month_previous_quarter = current_month - relativedelta(months=3)
                    previous_qtd_total_usage = 0
                    previous_qtd_amount = 0
                    previous_qtd_cost_per_use = 0
                    found_first_qtd_cost_per_use = True
                    for m in utils.month_range(start_of_previous_quarter, current_month_previous_quarter):
                        try:
                            u = SubscriptionCostPerUseStat.objects.get(
                                publisher_id=publisher_id,
                                membership_no=current_cost_per_use.membership_no,
                                bundle_name=current_cost_per_use.bundle_name,
                                usage_date=m,
                            )
                            previous_qtd_total_usage += u.total_usage
                            previous_qtd_amount += u.amoujnt
                            if m == start_of_previous_quarter:
                                found_first_qtd_cost_per_use = True
                        except SubscriptionCostPerUseStat.DoesNotExist:
                            if not found_first_qtd_cost_per_use:
                                break

                    if found_first_qtd_cost_per_use:
                        start_of_current_quarter = utils.start_of_quarter(current_month)
                        current_qtd_total_usage = 0
                        current_qtd_amount = 0
                        current_qtd_cost_per_use = 0
                        for m in utils.month_range(start_of_current_quarter, current_month):
                            try:
                                u = SubscriptionCostPerUseStat.objects.get(
                                    publisher_id=publisher_id,
                                    membership_no=current_cost_per_use.membership_no,
                                    bundle_name=current_cost_per_use.bundle_name,
                                    usage_date=m,
                                )
                                previous_qtd_total_usage += u.total_usage
                                previous_qtd_amount += u.amoujnt
                            except SubscriptionCostPerUseStat.DoesNotExist:
                                pass

                        if previous_qtd_total_usage:
                            previous_qtd_cost_per_use = previous_qtd_amount / previous_qtd_total_usage

                        if current_qtd_total_usage:
                            current_qtd_cost_per_use = current_qtd_amount / current_qtd_total_usage

                        absolute_qtd_delta = current_qtd_cost_per_use - previous_qtd_cost_per_use
                        if previous_qtd_cost_per_use:
                            percentage_qtd_delta = absolute_qtd_delta / previous_qtd_cost_per_use
                        else:
                            percentage_qtd_delta = 0.0

                        SubscriptionCostPerUseStatDelta.objects(
                            publisher_id=publisher_id,
                            membership_no=current_cost_per_use.membership_no,
                            bundle_name=current_cost_per_use.bundle_name,
                            usage_date=current_month,
                            time_slice='qtd',
                        ).update(
                            previous_cost_per_use=previous_qtd_cost_per_use,
                            current_cost_per_use=current_qtd_cost_per_use,
                            absolute_delta=absolute_qtd_delta,
                            percentage_delta=percentage_qtd_delta,
                        )

                    #
                    # time_slice == 'ytd' (year-to-date)
                    #

                    # start_of_previous_year = datetime.date(current_month.year - 1, 1, 1)
                    # current_month_previous_year = datetime.date(current_month.year - 1, current_month.month, 1)
                    # previous_ytd_usage = 0
                    # found_first_ytd_usage = True
                    # for m in utils.month_range(start_of_previous_year, current_month_previous_year):
                    #     try:
                    #         u = InstitutionUsageStat.objects.get(
                    #             publisher_id=publisher_id,
                    #             counter_type=current_cost_per_use.counter_type,
                    #             journal=current_cost_per_use.journal,
                    #             subscriber_id=current_cost_per_use.subscriber_id,
                    #             usage_date=m,
                    #             usage_category=current_cost_per_use.usage_category,
                    #         )
                    #         previous_ytd_usage += u.usage
                    #         if m == start_of_previous_year:
                    #             found_first_ytd_usage = True
                    #     except InstitutionUsageStat.DoesNotExist:
                    #         if not found_first_ytd_usage:
                    #             break
                    #
                    # if found_first_ytd_usage:
                    #     start_of_current_year = datetime.date(current_month.year, 1, 1)
                    #     current_ytd_usage = 0
                    #     for m in utils.month_range(start_of_current_year, current_month):
                    #         try:
                    #             u = InstitutionUsageStat.objects.get(
                    #                 publisher_id=publisher_id,
                    #                 counter_type=current_cost_per_use.counter_type,
                    #                 journal=current_cost_per_use.journal,
                    #                 subscriber_id=current_cost_per_use.subscriber_id,
                    #                 usage_date=m,
                    #                 usage_category=current_cost_per_use.usage_category,
                    #             )
                    #             current_ytd_usage += u.usage
                    #         except InstitutionUsageStat.DoesNotExist:
                    #             pass
                    #
                    #     absolute_ytd_delta = current_ytd_usage - previous_ytd_usage
                    #     if previous_ytd_usage:
                    #         percentage_ytd_delta = absolute_ytd_delta / previous_ytd_usage
                    #     else:
                    #         percentage_ytd_delta = 0.0
                    #
                    #     InstitutionUsageStatDelta.objects(
                    #         publisher_id=publisher_id,
                    #         counter_type=current_cost_per_use.counter_type,
                    #         journal=current_cost_per_use.journal,
                    #         subscriber_id=current_cost_per_use.subscriber_id,
                    #         usage_date=current_month,
                    #         usage_category=current_cost_per_use.usage_category,
                    #         time_slice='ytd',
                    #     ).update(
                    #         previous_usage=previous_ytd_usage,
                    #         current_usage=current_ytd_usage,
                    #         absolute_delta=absolute_ytd_delta,
                    #         percentage_delta=percentage_ytd_delta,
                    #     )

            else:
                tlogger.info('No stats found')

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id)

        return {
            'count': count
        }
