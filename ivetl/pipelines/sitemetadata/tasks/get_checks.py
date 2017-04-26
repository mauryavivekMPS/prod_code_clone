import os
import codecs
import json
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.connectors import PingdomConnector
from ivetl.common import common


@app.task
class GetChecksTask(Task):
    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        target_file_name = os.path.join(work_folder, "%s_uptimechecks_target.tab" % publisher_id)

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

                tlogger.info('Getting check details for check %s' % check['id'])

                pingdom = pingdom_connector_by_name[check['account']]
                check_with_details = pingdom.get_check_details(check['id'])

                # store the account
                check_with_details['account'] = check['account']

                # write out to target file
                row = "%s\t%s\n" % (check['id'], json.dumps(check_with_details))
                target_file.write(row)

        task_args['count'] = count
        task_args['input_file'] = target_file_name
        return task_args
