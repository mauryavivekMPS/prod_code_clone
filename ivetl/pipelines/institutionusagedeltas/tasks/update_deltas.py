import datetime
from dateutil.relativedelta import relativedelta
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import InstitutionUsageStatComposite, InstitutionUsageStatDelta, InstitutionUsageJournal, SystemGlobal
from ivetl import utils
from ivetl.common import common


@app.task
class UpdateDeltasTask(Task):
    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        cluster = Cluster(common.CASSANDRA_IP_LIST)
        session = cluster.connect()

        now = datetime.datetime.now()

        from_date = self.from_json_date(task_args.get('from_date'))
        to_date = self.from_json_date(task_args.get('to_date'))

        earliest_date_value_global_name = publisher_id + '_institution_usage_stat_earliest_date_value'
        earliest_date_dirty_global_name = publisher_id + '_institution_usage_stat_earliest_date_dirty'

        if not from_date:
            try:
                from_date = SystemGlobal.objects.get(name=earliest_date_value_global_name).date_value.date()
            except SystemGlobal.DoesNotExist:
                from_date = datetime.date(2013, 1, 1)

        earliest_date_global = SystemGlobal.objects(name=earliest_date_value_global_name)
        earliest_date_global.update(date_value=from_date)

        SystemGlobal.objects(name=earliest_date_dirty_global_name).update(int_value=0)

        if not to_date:
            to_date = datetime.date(now.year, now.month, 1)

        total_count = utils.get_record_count_estimate(publisher_id, product_id, pipeline_id, self.short_name)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0

        stopped = False

        all_journals = InstitutionUsageJournal.objects.filter(publisher_id=publisher_id)

        for current_month in utils.month_range(from_date, to_date):

            tlogger.info('Processing month %s' % current_month.strftime('%Y-%m'))

            for journal in all_journals:

                # select all usage for the current (iterated) month
                all_current_month_usage_sql = """
                  select subscriber_id, journal, counter_type, usage_category, usage_date, usage
                  from impactvizor.institution_usage_stat_composite
                  where publisher_id = %s
                  and counter_type = %s
                  and journal = %s
                  and usage_date = %s
                  limit 10000000
                """

                all_current_month_usage_statement = SimpleStatement(all_current_month_usage_sql, fetch_size=1000)

                for current_usage in session.execute(all_current_month_usage_statement, (publisher_id, journal.counter_type, journal.journal, current_month)):

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
                        previous_usage = InstitutionUsageStatComposite.objects.get(
                            publisher_id=publisher_id,
                            counter_type=current_usage.counter_type,
                            journal=current_usage.journal,
                            subscriber_id=current_usage.subscriber_id,
                            usage_date=previous_month,
                            usage_category=current_usage.usage_category,
                        )

                        absolute_delta = current_usage.usage - previous_usage.usage
                        if previous_usage.usage:
                            percentage_delta = absolute_delta / previous_usage.usage
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

                    except InstitutionUsageStatComposite.DoesNotExist:
                        pass

                    #
                    # time_slice == 'ytd' (year-to-date)
                    #

                    start_of_previous_year = datetime.date(current_month.year - 1, 1, 1)
                    current_month_previous_year = datetime.date(current_month.year - 1, current_month.month, 1)
                    previous_ytd_usage = 0
                    found_first_ytd_usage = True
                    for m in utils.month_range(start_of_previous_year, current_month_previous_year):
                        try:
                            u = InstitutionUsageStatComposite.objects.get(
                                publisher_id=publisher_id,
                                counter_type=current_usage.counter_type,
                                journal=current_usage.journal,
                                subscriber_id=current_usage.subscriber_id,
                                usage_date=m,
                                usage_category=current_usage.usage_category,
                            )
                            previous_ytd_usage += u.usage
                            if m == start_of_previous_year:
                                found_first_ytd_usage = True
                        except InstitutionUsageStatComposite.DoesNotExist:
                            if not found_first_ytd_usage:
                                break

                    if found_first_ytd_usage:
                        start_of_current_year = datetime.date(current_month.year, 1, 1)
                        current_ytd_usage = 0
                        for m in utils.month_range(start_of_current_year, current_month):
                            try:
                                u = InstitutionUsageStatComposite.objects.get(
                                    publisher_id=publisher_id,
                                    counter_type=current_usage.counter_type,
                                    journal=current_usage.journal,
                                    subscriber_id=current_usage.subscriber_id,
                                    usage_date=m,
                                    usage_category=current_usage.usage_category,
                                )
                                current_ytd_usage += u.usage
                            except InstitutionUsageStatComposite.DoesNotExist:
                                pass

                        absolute_ytd_delta = current_ytd_usage - previous_ytd_usage
                        if previous_ytd_usage:
                            percentage_ytd_delta = absolute_ytd_delta / previous_ytd_usage
                        else:
                            percentage_ytd_delta = 0.0

                        InstitutionUsageStatDelta.objects(
                            publisher_id=publisher_id,
                            counter_type=current_usage.counter_type,
                            journal=current_usage.journal,
                            subscriber_id=current_usage.subscriber_id,
                            usage_date=current_month,
                            usage_category=current_usage.usage_category,
                            time_slice='ytd',
                        ).update(
                            previous_usage=previous_ytd_usage,
                            current_usage=current_ytd_usage,
                            absolute_delta=absolute_ytd_delta,
                            percentage_delta=percentage_ytd_delta,
                        )

                    if stopped:
                        break

        if not stopped:
            self.pipeline_ended(
                publisher_id,
                product_id,
                pipeline_id,
                job_id,
                tlogger,
                show_alerts=task_args['show_alerts']
            )

        try:
            dirty_flag = SystemGlobal.objects.get(name=earliest_date_dirty_global_name).int_value
        except SystemGlobal.DoesNotExist:
            dirty_flag = 0

        if not dirty_flag:
            earliest_date_global.delete()

        task_args['count'] = count
        return task_args
