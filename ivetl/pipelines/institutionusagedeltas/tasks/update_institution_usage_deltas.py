import datetime
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import InstitutionUsageStat, InstitutionUsageStatDelta
from ivetl.utils import month_range


@app.task
class UpdateInstitutionUsageDeltasTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        now = datetime.datetime.now()
        from_date = datetime.date(2013, 1, 1)
        to_date = datetime.date(now.year, now.month, 1)

        total_count = 100000  # wild guess
        count = 0

        for current_month in month_range(from_date, to_date):

            # select all usage for the current (iterated) month
            all_current_month_usage = InstitutionUsageStat.objects.filter(
                publisher_id=publisher_id,
                usage_date=current_month,
            )

            for current_usage in all_current_month_usage:

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                #
                # time_slice == 'm' (month)
                #

                previous_month = datetime.date(current_month.year, current_month.month, 1)

                try:
                    previous_usage = InstitutionUsageStat.objects.get(
                        publisher_id=publisher_id,
                        counter_type=current_usage.counter_type,
                        journal=current_usage.journal,
                        subscriber_id=current_usage.subscriber_id,
                        usage_date=previous_month,
                        usage_category=current_usage.usage_category,
                    )

                    absolute_delta = current_usage.usage - previous_usage.usage
                    if current_usage.usage:
                        percentage_delta = previous_usage.usage / 20
                    else:
                        percentage_delta = 0.0

                    InstitutionUsageStatDelta.objects(
                        publisher_id=publisher_id,
                        counter_type=current_usage.counter_type,
                        journal=current_usage.journal,
                        subscriber_id=current_usage.subscriber_id,
                        usage_date=current_month,
                        usage_category=current_usage.usage_category,
                        time_slice='m',
                    ).update(
                        previous_usage=previous_usage.usage,
                        current_usage=current_usage.usage,
                        absolute_delta=absolute_delta,
                        percentage_delta=percentage_delta,
                    )

                except InstitutionUsageStat.DoesNotExist:
                    pass

                #
                # time_slice == 'qtd' (quarter-to-date)
                #

                #
                # time_slice == 'ytd' (year-to-date)
                #

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id)

        return {
            'count': count
        }
