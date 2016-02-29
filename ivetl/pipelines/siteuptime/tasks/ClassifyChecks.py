from ivetl.celery import app
from ivetl.pipelines.task import Task


@app.task
class ClassifyChecks(Task):
    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        pass
