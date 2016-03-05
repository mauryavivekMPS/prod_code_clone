import os
import codecs
import json
import datetime
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.connectors import PingdomConnector
from ivetl.common import common
from ivetl.models import System_Global


@app.task
class GetStats(Task):
    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        from_date = task_args['from_date']
        to_date = task_args['to_date']

        target_file_name = os.path.join(work_folder, "%s_uptimechecks_target.tab" % publisher_id)

        today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)

        if from_date:
            from_date = datetime.datetime.combine(from_date, datetime.time.min)

        if to_date:
            to_date = datetime.datetime.combine(to_date, datetime.time.min)

        if not from_date:
            try:
                # get last processed day
                last_uptime_day_processed = System_Global.objects.get(name=pipeline_id + '_high_water').date_value
            except System_Global.DoesNotExist:
                # default to two days ago
                last_uptime_day_processed = today - datetime.timedelta(2)

            from_date = last_uptime_day_processed

        if from_date > today - datetime.timedelta(1):
            tlogger.error('Invalid date range: The from date must before yesterday.')
            raise Exception

        if not to_date:
            to_date = today - datetime.timedelta(1)

        if to_date < from_date:
            tlogger.error('Invalid date range: The date range must be at least one day.')
            raise Exception

        tlogger.info('Using date range: %s to %s' % (from_date.strftime('%Y-%m-%d'), to_date.strftime('%Y-%m-%d')))

        with codecs.open(target_file_name, 'w', 'utf-16') as target_file:
            target_file.write('CHECK_ID\tDATA\n')

            total_count = 0

            pingdom_connector_by_name = {}

            # get all check basics first (fast) and then we can communicate a total
            all_checks = []
            for account in common.PINGDOM_ACCOUNTS:
                pingdom = PingdomConnector(account['email'], account['password'], account['api_key'], tlogger=tlogger)
                pingdom_connector_by_name[account['name']] = pingdom

                tlogger.info('Loaded pingdom connector for account: %s' % account['name'])

                account_checks = pingdom.get_checks()
                for check in account_checks:
                    check['account'] = account['name']
                    all_checks.append(check)

                tlogger.info('Found %s checks for %s' % (len(account_checks), account['name']))

                total_count += len(account_checks)

            self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

            count = 0

            # now get details and stats (slower)
            for check in all_checks:

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                tlogger.info('Getting stats for check %s' % check['id'])

                pingdom = pingdom_connector_by_name[check['account']]
                check_with_stats = pingdom.get_check_stats(check['id'], from_date, to_date)

                # stringify the dates
                for stat in check_with_stats['stats']:
                    stat['date'] = stat['date'].strftime('%Y-%m-%d')

                # write out to target file
                row = "%s\t%s\n" % (check['id'], json.dumps(check_with_stats))
                target_file.write(row)

        return {
            'count': total_count,
            'input_file': target_file_name,
            'from_date': from_date,
            'to_date': to_date,
        }
