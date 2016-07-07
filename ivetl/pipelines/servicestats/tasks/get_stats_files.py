import re
import os
import shutil
import datetime
import spur
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import System_Global


@app.task
class GetStatsFilesTask(Task):
    HOSTNAME = 'dw-work-02.highwire.org'
    USERNAME = 'netsite'
    PASSWORD = 'F!b57g0v'
    LOG_FILE_DIR = '/var/log/logstat'

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        from_date = self.from_json_date(task_args.get('from_date'))
        to_date = self.from_json_date(task_args.get('to_date'))

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
            tlogger.error('Invalid date range: The from date must be before yesterday.')
            raise Exception

        if not to_date:
            to_date = today - datetime.timedelta(1)

        if to_date < from_date:
            tlogger.error('Invalid date range: The date range must be at least one day.')
            raise Exception

        tlogger.info('Using date range: %s to %s' % (from_date.strftime('%Y-%m-%d'), to_date.strftime('%Y-%m-%d')))


        # today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
        #
        # if from_date:
        #     from_date = datetime.datetime.combine(from_date, datetime.time.min)
        #
        # if to_date:
        #     to_date = datetime.datetime.combine(to_date, datetime.time.min)
        #
        # def _previous_quarter(ref):
        #     if ref.month < 4:
        #         return datetime.datetime(ref.year - 1, 10, 1), datetime.datetime(ref.year - 1, 12, 31)
        #     elif ref.month < 7:
        #         return datetime.datetime(ref.year, 1, 1), datetime.datetime(ref.year, 3, 31)
        #     elif ref.month < 10:
        #         return datetime.datetime(ref.year, 4, 1), datetime.datetime(ref.year, 6, 30)
        #     else:
        #         return datetime.datetime(ref.year, 7, 1), datetime.datetime(ref.year, 9, 30)
        #
        # if not (from_date or to_date):
        #     from_date, to_date = _previous_quarter(today)
        #
        # if from_date > today - datetime.timedelta(1):
        #     tlogger.error('Invalid date range: The from date must be before yesterday.')
        #     raise Exception
        #
        # if not to_date:
        #     to_date = today - datetime.timedelta(1)
        #
        # if to_date < from_date:
        #     tlogger.error('Invalid date range: The date range must be at least one day.')
        #     raise Exception
        #
        # tlogger.info('Using date range: %s to %s' % (from_date.strftime('%Y-%m-%d'), to_date.strftime('%Y-%m-%d')))

        # journals_with_benchpress = [p.journal_code for p in Publisher_Journal.objects.filter(
        #     publisher_id=publisher_id,
        #     product_id='published_articles',
        #     use_benchpress=True
        # )]

        # total_count = len(journals_with_benchpress)
        # self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)
        #
        # files = []

        shell = spur.SshShell(
            hostname=self.HOSTNAME,
            username=self.USERNAME,
            password=self.PASSWORD,
            missing_host_key=spur.ssh.MissingHostKey.accept,
            shell_type=spur.ssh.ShellTypes.minimal
        )

        # get a full list of all the available files
        all_remote_files = [f for f in shell.run(['/bin/ls', self.LOG_FILE_DIR]).output.decode('utf-8').split('\n') if f]

        files = []

        for file_name in all_remote_files:
            remote_file_path = os.path.join(self.LOG_FILE_DIR, file_name)
            local_file_path = os.path.join(work_folder, file_name)
            with shell.open(remote_file_path, "rb") as remote_file:
                with open(local_file_path, "wb") as local_file:
                    shutil.copyfileobj(remote_file, local_file)

            files.append(local_file_path)

            tlogger.info('Retrieved file: %s' % local_file_path)

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id)

        return {
            'input_files': files,
            # 'count': total_count,
        }
