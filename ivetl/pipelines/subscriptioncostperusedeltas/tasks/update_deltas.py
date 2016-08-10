import datetime
from dateutil.relativedelta import relativedelta
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import InstitutionUsageStat, InstitutionUsageStatDelta
from ivetl import utils


@app.task
class UpdateDeltasTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        now = datetime.datetime.now()
        from_date = datetime.date(2013, 1, 1)
        to_date = datetime.date(now.year, now.month, 1)

        total_count = None
        count = 0

        # for current_month in utils.month_range(from_date, to_date):
        #
        #     tlogger.info('Processing month %s' % current_month.strftime('%Y-%m'))
        #
        #     # select all usage for the current (iterated) month
        #     all_current_month_usage = InstitutionUsageStat.objects.filter(
        #         publisher_id=publisher_id,
        #         usage_date=current_month,
        #     )
        #
        #     all_current_month_usage_count = all_current_month_usage.count()
        #
        #     if all_current_month_usage_count:
        #
        #         tlogger.info('Found %s records' % all_current_month_usage_count)
        #
        #         # estimate the total count
        #         if total_count is None:
        #             months_remaining = relativedelta(to_date, current_month).months + 1
        #             total_count = all_current_month_usage.count() * months_remaining
        #             self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)
        #
        #         for current_usage in all_current_month_usage:
        #
        #             count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
        #
        #             #
        #             # time_slice == 'm' (month)
        #             #
        #
        #             previous_month = datetime.date(current_month.year, current_month.month, 1)
        #
        #             try:
        #                 previous_usage = InstitutionUsageStat.objects.get(
        #                     publisher_id=publisher_id,
        #                     counter_type=current_usage.counter_type,
        #                     journal=current_usage.journal,
        #                     subscriber_id=current_usage.subscriber_id,
        #                     usage_date=previous_month,
        #                     usage_category=current_usage.usage_category,
        #                 )
        #
        #                 absolute_delta = current_usage.usage - previous_usage.usage
        #                 if previous_usage.usage:
        #                     percentage_delta = absolute_delta / previous_usage.usage
        #                 else:
        #                     percentage_delta = 0.0
        #
        #                 InstitutionUsageStatDelta.objects(
        #                     publisher_id=publisher_id,
        #                     counter_type=current_usage.counter_type,
        #                     journal=current_usage.journal,
        #                     subscriber_id=current_usage.subscriber_id,
        #                     usage_date=current_month,
        #                     usage_category=current_usage.usage_category,
        #                     time_slice='m',
        #                 ).update(
        #                     previous_usage=previous_usage.usage,
        #                     current_usage=current_usage.usage,
        #                     absolute_delta=absolute_delta,
        #                     percentage_delta=percentage_delta,
        #                 )
        #
        #             except InstitutionUsageStat.DoesNotExist:
        #                 pass
        #
        #             #
        #             # time_slice == 'qtd' (quarter-to-date)
        #             #
        #
        #             start_of_previous_quarter = utils.start_of_previous_quarter(current_month)
        #             current_month_previous_quarter = current_month - relativedelta(months=3)
        #             previous_qtd_usage = 0
        #             found_first_qtd_usage = True
        #             for m in utils.month_range(start_of_previous_quarter, current_month_previous_quarter):
        #                 try:
        #                     u = InstitutionUsageStat.objects.get(
        #                         publisher_id=publisher_id,
        #                         counter_type=current_usage.counter_type,
        #                         journal=current_usage.journal,
        #                         subscriber_id=current_usage.subscriber_id,
        #                         usage_date=m,
        #                         usage_category=current_usage.usage_category,
        #                     )
        #                     previous_qtd_usage += u.usage
        #                     if m == start_of_previous_quarter:
        #                         found_first_qtd_usage = True
        #                 except InstitutionUsageStat.DoesNotExist:
        #                     if not found_first_qtd_usage:
        #                         break
        #
        #             if found_first_qtd_usage:
        #                 start_of_current_quarter = utils.start_of_quarter(current_month)
        #                 current_qtd_usage = 0
        #                 for m in utils.month_range(start_of_current_quarter, current_month):
        #                     try:
        #                         u = InstitutionUsageStat.objects.get(
        #                             publisher_id=publisher_id,
        #                             counter_type=current_usage.counter_type,
        #                             journal=current_usage.journal,
        #                             subscriber_id=current_usage.subscriber_id,
        #                             usage_date=m,
        #                             usage_category=current_usage.usage_category,
        #                         )
        #                         current_qtd_usage += u.usage
        #                     except InstitutionUsageStat.DoesNotExist:
        #                         pass
        #
        #                 absolute_qtd_delta = current_qtd_usage - previous_qtd_usage
        #                 if previous_qtd_usage:
        #                     percentage_qtd_delta = absolute_qtd_delta / previous_qtd_usage
        #                 else:
        #                     percentage_qtd_delta = 0.0
        #
        #                 InstitutionUsageStatDelta.objects(
        #                     publisher_id=publisher_id,
        #                     counter_type=current_usage.counter_type,
        #                     journal=current_usage.journal,
        #                     subscriber_id=current_usage.subscriber_id,
        #                     usage_date=current_month,
        #                     usage_category=current_usage.usage_category,
        #                     time_slice='qtd',
        #                 ).update(
        #                     previous_usage=previous_qtd_usage,
        #                     current_usage=current_qtd_usage,
        #                     absolute_delta=absolute_qtd_delta,
        #                     percentage_delta=percentage_qtd_delta,
        #                 )
        #
        #             #
        #             # time_slice == 'ytd' (year-to-date)
        #             #
        #
        #             start_of_previous_year = datetime.date(current_month.year - 1, 1, 1)
        #             current_month_previous_year = datetime.date(current_month.year - 1, current_month.month, 1)
        #             previous_ytd_usage = 0
        #             found_first_ytd_usage = True
        #             for m in utils.month_range(start_of_previous_year, current_month_previous_year):
        #                 try:
        #                     u = InstitutionUsageStat.objects.get(
        #                         publisher_id=publisher_id,
        #                         counter_type=current_usage.counter_type,
        #                         journal=current_usage.journal,
        #                         subscriber_id=current_usage.subscriber_id,
        #                         usage_date=m,
        #                         usage_category=current_usage.usage_category,
        #                     )
        #                     previous_ytd_usage += u.usage
        #                     if m == start_of_previous_year:
        #                         found_first_ytd_usage = True
        #                 except InstitutionUsageStat.DoesNotExist:
        #                     if not found_first_ytd_usage:
        #                         break
        #
        #             if found_first_ytd_usage:
        #                 start_of_current_year = datetime.date(current_month.year, 1, 1)
        #                 current_ytd_usage = 0
        #                 for m in utils.month_range(start_of_current_year, current_month):
        #                     try:
        #                         u = InstitutionUsageStat.objects.get(
        #                             publisher_id=publisher_id,
        #                             counter_type=current_usage.counter_type,
        #                             journal=current_usage.journal,
        #                             subscriber_id=current_usage.subscriber_id,
        #                             usage_date=m,
        #                             usage_category=current_usage.usage_category,
        #                         )
        #                         current_ytd_usage += u.usage
        #                     except InstitutionUsageStat.DoesNotExist:
        #                         pass
        #
        #                 absolute_ytd_delta = current_ytd_usage - previous_ytd_usage
        #                 if previous_ytd_usage:
        #                     percentage_ytd_delta = absolute_ytd_delta / previous_ytd_usage
        #                 else:
        #                     percentage_ytd_delta = 0.0
        #
        #                 InstitutionUsageStatDelta.objects(
        #                     publisher_id=publisher_id,
        #                     counter_type=current_usage.counter_type,
        #                     journal=current_usage.journal,
        #                     subscriber_id=current_usage.subscriber_id,
        #                     usage_date=current_month,
        #                     usage_category=current_usage.usage_category,
        #                     time_slice='ytd',
        #                 ).update(
        #                     previous_usage=previous_ytd_usage,
        #                     current_usage=current_ytd_usage,
        #                     absolute_delta=absolute_ytd_delta,
        #                     percentage_delta=percentage_ytd_delta,
        #                 )
        #
        #     else:
        #         tlogger.info('No stats found')

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id)

        return {
            'count': count
        }
