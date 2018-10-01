import os
import shutil
import spur
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.common import common
from ivetl import utils


@app.task
class GetStatsFilesTask(Task):
    HOSTNAME = 'dw-work-02.highwire.org'
    LOG_FILE_DIR = os.environ.get('IVETL_WORKING_DIR', '/var/log/logstat')
    LOG_FILE_EXTENSION = '.log'

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        from_date = self.from_json_date(task_args.get('from_date'))
        to_date = self.from_json_date(task_args.get('to_date'))
        from_date, to_date = utils.get_from_to_dates_with_high_water(product_id, pipeline_id, publisher_id, from_date, to_date)
        tlogger.info('Using date range: %s to %s' % (from_date.strftime('%Y-%m-%d'), to_date.strftime('%Y-%m-%d')))

        all_file_names = [d.strftime('%Y-%m-%d' + self.LOG_FILE_EXTENSION) for d in utils.day_range(from_date, to_date)]

        total_count = len(all_file_names)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)
        count = 0

        shell = spur.SshShell(
            hostname=self.HOSTNAME,
            username=common.NETSITE_USERNAME,
            password=common.NETSITE_PASSWORD,
            missing_host_key=spur.ssh.MissingHostKey.accept,
            shell_type=spur.ssh.ShellTypes.minimal
        )

        # get a full list of all the available files
        all_remote_files = [f for f in shell.run(['/bin/ls', self.LOG_FILE_DIR]).output.decode('utf-8').split('\n') if f]

        files = []

        for file_name in all_file_names:

            count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

            if file_name not in all_remote_files:
                tlogger.info('Could not find file for date %s on remote server' % file_name.split('.')[0])
                continue

            remote_file_path = os.path.join(self.LOG_FILE_DIR, file_name)
            local_file_path = os.path.join(work_folder, file_name)
            with shell.open(remote_file_path, "rb") as remote_file:
                with open(local_file_path, "wb") as local_file:
                    shutil.copyfileobj(remote_file, local_file)

            files.append(local_file_path)

            tlogger.info('Retrieved file: %s' % file_name)

        task_args['from_date'] = self.to_json_date(from_date)
        task_args['to_date'] = self.to_json_date(to_date)
        task_args['input_files'] = files
        task_args['count'] = total_count

        return task_args
