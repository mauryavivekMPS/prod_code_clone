__author__ = 'johnm'

from ivetl.celery import app
from ivetl.pipelines.task import Task


@app.task
class ValidateArticleDataFile(Task):
    pipeline_name = "custom_article_data"

    def run_task(self, publisher_id, job_id, work_folder, tlogger, task_args):
        print("Running validate for %s" % publisher_id)
        return {}
