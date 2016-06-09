import csv
import json
import codecs
import datetime
from dateutil.parser import parse
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import Uptime_Check_Stat, Uptime_Check_Metadata, System_Global
from ivetl.alerts import run_alerts, send_alert_notifications, get_all_params_for_check
from ivetl import utils

@app.task
class InsertJR2IntoCassandra(Task):
    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        return {}

        # file = task_args['input_file']
        # total_count = task_args['count']
        # to_date = task_args['to_date']
        #
        # self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)
        #
        # # figure out what the longest window is so we can get data for alerts
        # all_params = get_all_params_for_check(check_id='site-uptime-below-threshold', publisher_id=publisher_id)
        # longest_window = 0
        # for window in [p['window_days'] for p in all_params]:
        #     if window > longest_window:
        #         longest_window = window
        #
        # alert_from_date = to_date - datetime.timedelta(longest_window)
        #
        # count = 0
        # with codecs.open(file, encoding="utf-16") as tsv:
        #     for line in csv.reader(tsv, delimiter="\t"):
        #
        #         count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
        #         if count == 1:
        #             continue
        #
        #         check = json.loads(line[1])
        #
        #         stats_by_date = {stat['date'] for stat in check['stats']}
        #
        #         for stat in check['stats']:
        #
        #             date = parse(stat['date'])
        #
        #             Uptime_Check_Stat.objects(
        #                 publisher_id=publisher_id,
        #                 check_id=check['id'],
        #                 check_date=date,
        #             ).update(
        #                 avg_response_ms=stat['avg_response_ms'],
        #                 total_up_sec=stat['total_up_sec'],
        #                 total_down_sec=stat['total_down_sec'],
        #                 total_unknown_sec=stat['total_unknown_sec'],
        #             )
        #
        #         if task_args['run_daily_uptime_alerts']:
        #
        #             # collect uptime for previous n days
        #             uptimes = []
        #             for date in utils.date_range(alert_from_date, to_date):
        #
        #                 # for testing
        #                 # if len(uptimes) in [2, 3]:
        #                 #     uptimes.append(70000)
        #                 #     continue
        #
        #                 if date in stats_by_date:
        #                     uptimes.append(stat['total_up_sec'] + stat['total_unknown_sec'])
        #                 else:
        #                     try:
        #                         stat = Uptime_Check_Stat.objects.get(
        #                             publisher_id=publisher_id,
        #                             check_id=check['id'],
        #                             check_date=date,
        #                         )
        #                         uptimes.append(stat.total_up_sec)
        #                     except Uptime_Check_Stat.DoesNotExist:
        #                         uptimes.append(None)
        #
        #             # get metadata for check
        #             check_metadata = Uptime_Check_Metadata.objects.get(
        #                 publisher_id=publisher_id,
        #                 check_id=check['id'],
        #             )
        #
        #             run_alerts(
        #                 check_ids=['site-uptime-below-threshold'],
        #                 publisher_id=publisher_id,
        #                 product_id=product_id,
        #                 pipeline_id=pipeline_id,
        #                 job_id=job_id,
        #                 extra_values={
        #                     'uptimes': uptimes,
        #                     'from_date': alert_from_date.strftime('%Y-%m-%d'),
        #                     'to_date': to_date.strftime('%Y-%m-%d'),
        #                     'check_id': check['id'],
        #                     'check_name': check_metadata.check_name,
        #                     'check_type': check_metadata.check_type,
        #                     'site_code': check_metadata.site_code,
        #                     'site_type': check_metadata.site_type,
        #                     'site_platform': check_metadata.site_platform,
        #                     'pingdom_account': check_metadata.pingdom_account,
        #                 }
        #             )
        #
        # # update high water mark if the new data is more recent
        # try:
        #     current_high_water = System_Global.objects(name=pipeline_id + '_high_water').date_value
        # except:
        #     current_high_water = datetime.datetime.min
        #
        # if to_date > current_high_water:
        #     System_Global.objects(name=pipeline_id + '_high_water').update(date_value=to_date)
        #
        # if task_args['run_daily_uptime_alerts']:
        #     send_alert_notifications(
        #         check_ids=['site-uptime-below-threshold'],
        #         publisher_id=publisher_id,
        #         product_id=product_id,
        #         pipeline_id=pipeline_id,
        #         job_id=job_id,
        #     )
        #
        # self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id)
        #
        # return {
        #     'count': count
        # }
