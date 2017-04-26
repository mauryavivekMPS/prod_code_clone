import datetime
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import UptimeCheckMetadata, UptimeCheckStat
from ivetl.alerts import run_alerts, send_alert_notifications, get_all_params_for_check
from ivetl import utils


@app.task
class RunWeeklyAlertsTask(Task):
    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        to_date = self.from_json_date(task_args['to_date'])

        # figure out what the longest window is so we can get data for alerts
        all_params = get_all_params_for_check(check_id='site-uptime-below-threshold', publisher_id=publisher_id)
        longest_window = 0
        for window in [p['window_days'] for p in all_params]:
            if window > longest_window:
                longest_window = window

        if type(to_date) == datetime.datetime:
            to_date = to_date.date()

        alert_from_date = to_date - datetime.timedelta(longest_window)

        all_checks = UptimeCheckMetadata.objects.filter(publisher_id=publisher_id)

        count = 0
        total_count = len(all_checks)

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        for check in all_checks:

            count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

            # collect uptime for previous n days
            uptimes = []
            for date in utils.day_range(alert_from_date, to_date):

                # for testing...
                # if len(uptimes) in [2, 3]:
                #     uptimes.append(70000)
                #     continue

                try:
                    stat = UptimeCheckStat.objects.get(
                        publisher_id=publisher_id,
                        check_id=check.check_id,
                        check_date=date,
                    )
                    uptimes.append(stat.total_up_sec + stat.total_unknown_sec)
                except UptimeCheckStat.DoesNotExist:
                    uptimes.append(None)

            # get metadata for check
            check_metadata = UptimeCheckMetadata.objects.get(
                publisher_id=publisher_id,
                check_id=check.check_id,
            )

            run_alerts(
                check_ids=['site-uptime-below-threshold'],
                publisher_id=publisher_id,
                product_id=product_id,
                pipeline_id=pipeline_id,
                job_id=job_id,
                extra_values={
                    'uptimes': uptimes,
                    'from_date': alert_from_date.strftime('%Y-%m-%d'),
                    'to_date': to_date.strftime('%Y-%m-%d'),
                    'check_id': check.check_id,
                    'check_name': check_metadata.check_name,
                    'check_type': check_metadata.check_type,
                    'site_code': check_metadata.site_code,
                    'site_type': check_metadata.site_type,
                    'site_platform': check_metadata.site_platform,
                    'pingdom_account': check_metadata.pingdom_account,
                    'publisher_name': check_metadata.publisher_name,
                }
            )

        send_alert_notifications(
            check_ids=['site-uptime-below-threshold'],
            publisher_id=publisher_id,
            product_id=product_id,
            pipeline_id=pipeline_id,
            job_id=job_id,
        )

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, tlogger, show_alerts=task_args['show_alerts'])

        task_args['count'] = total_count

        return task_args
