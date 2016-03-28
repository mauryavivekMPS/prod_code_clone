import re
import os
import shutil
import spur
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import Publisher_Journal


@app.task
class GetRejectedArticlesFromBenchPressTask(Task):
    HOSTNAME = 'hw-bp-cron-dev-1.highwire.org'
    USERNAME = 'netsite'
    PASSWORD = 'Pch33br@in'
    SCRIPT = '/mstr/maint/vizor/vizor_request.pl'

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        journals_with_benchpress = [p.journal_code for p in Publisher_Journal.objects.filter(
            publisher_id=publisher_id,
            product_id='published_articles',
            use_benchpress=True
        )]

        start_date = '01/01/2016'
        end_date = '01/31/2016'

        total_count = len(journals_with_benchpress)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        files = []

        if journals_with_benchpress:

            shell = spur.SshShell(
                hostname=self.HOSTNAME,
                username=self.USERNAME,
                password=self.PASSWORD,
                missing_host_key=spur.ssh.MissingHostKey.accept
            )

            count = 0

            for journal_code in journals_with_benchpress:
                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                tlogger.info('Looking for file for journal: %s' % journal_code)

                result = shell.run([self.SCRIPT, '-b', start_date, '-e', end_date, '-j', journal_code, '-p'])

                output_file_match = re.search(r'Data file: (/.*\.txt)', result.output.decode('utf-8'))
                if output_file_match and output_file_match.groups():

                    output_file_path = output_file_match.groups()[0]
                    output_file_name = os.path.basename(output_file_path)
                    local_file_path = os.path.join(work_folder, output_file_name)

                    with shell.open(output_file_path, "r") as remote_file:
                        with open(local_file_path, "w") as local_file:
                            shutil.copyfileobj(remote_file, local_file)

                    files.append(local_file_path)

                    tlogger.info('Retrieved file: %s' % output_file_name)

        return {
            'input_files': files,
            'count': total_count,
        }
