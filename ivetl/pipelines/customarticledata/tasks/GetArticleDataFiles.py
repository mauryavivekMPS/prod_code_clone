from ivetl.celery import app
from ivetl.pipelines.task import Task


@app.task
class GetArticleDataFiles(Task):
    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        return self.run_get_files_task(publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args)
