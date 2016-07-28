import re
import os
import shutil
import datetime
import spur
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import PublisherJournal
from ivetl.common import common

@app.task
class GetRejectedArticlesFromBenchPressTask(Task):
    HOSTNAME = 'hw-bp-cron-dev-1.highwire.org'
    SCRIPT = '/mstr/maint/vizor/vizor_request.pl'

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        from_date = task_args.get('from_date')
        to_date = task_args.get('to_date')

        today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)

        if from_date:
            from_date = datetime.datetime.combine(from_date, datetime.time.min)

        if to_date:
            to_date = datetime.datetime.combine(to_date, datetime.time.min)

        def _previous_quarter(ref):
            if ref.month < 4:
                return datetime.datetime(ref.year - 1, 10, 1), datetime.datetime(ref.year - 1, 12, 31)
            elif ref.month < 7:
                return datetime.datetime(ref.year, 1, 1), datetime.datetime(ref.year, 3, 31)
            elif ref.month < 10:
                return datetime.datetime(ref.year, 4, 1), datetime.datetime(ref.year, 6, 30)
            else:
                return datetime.datetime(ref.year, 7, 1), datetime.datetime(ref.year, 9, 30)

        if not (from_date or to_date):
            from_date, to_date = _previous_quarter(today)

        if from_date > today - datetime.timedelta(1):
            tlogger.error('Invalid date range: The from date must be before yesterday.')
            raise Exception

        if not to_date:
            to_date = today - datetime.timedelta(1)

        if to_date < from_date:
            tlogger.error('Invalid date range: The date range must be at least one day.')
            raise Exception

        tlogger.info('Using date range: %s to %s' % (from_date.strftime('%Y-%m-%d'), to_date.strftime('%Y-%m-%d')))

        journals_with_benchpress = [p.journal_code for p in PublisherJournal.objects.filter(
            publisher_id=publisher_id,
            product_id='published_articles',
            use_benchpress=True
        )]

        total_count = len(journals_with_benchpress)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        files = []

        if journals_with_benchpress:

            shell = spur.SshShell(
                hostname=self.HOSTNAME,
                username=common.NETSITE_USERNAME,
                password=common.NETSITE_PASSWORD,
                missing_host_key=spur.ssh.MissingHostKey.accept
            )

            count = 0

            for journal_code in journals_with_benchpress:
                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                tlogger.info('Looking for file for journal: %s' % journal_code)

                result = shell.run([self.SCRIPT, '-b', from_date.strftime('%m/%d/%Y'), '-e', to_date.strftime('%m/%d/%Y'), '-j', journal_code, '-p'])
                result_text = result.output.decode('utf-8')

                output_file_match = re.search(r'Data file: (/.*\.txt)', result_text)
                if output_file_match and output_file_match.groups():

                    output_file_path = output_file_match.groups()[0]
                    output_file_name = os.path.basename(output_file_path)
                    local_file_path = os.path.join(work_folder, output_file_name)

                    with shell.open(output_file_path, "rb") as remote_file:
                        with open(local_file_path, "wb") as local_file:
                            shutil.copyfileobj(remote_file, local_file)

                    files.append(local_file_path)

                    tlogger.info('Retrieved file: %s' % output_file_name)

                else:
                    tlogger.error('Unexpected output from benchpress script: %s' % result_text)
                    raise Exception

        return {
            'input_files': files,
            'count': total_count,
        }
