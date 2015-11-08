import os
import shutil
from ivetl.celery import app
from ivetl.pipelines.task import Task


@app.task
class GetArticleDataFiles(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        preserve_incoming_files = task_args.get('preserve_incoming_files', False)

        total_count = len(task_args['uploaded_files'])
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0

        files = []
        for source_file in task_args['uploaded_files']:

            count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

            # move (or copy) files from incoming to current task folder
            if preserve_incoming_files:
                shutil.copy(source_file, work_folder)
            else:
                shutil.move(source_file, work_folder)

            # compile a list of files for the next task
            files.append(os.path.join(work_folder, os.path.basename(source_file)))

        return {
            'input_files': files,
            'count': count,
        }
