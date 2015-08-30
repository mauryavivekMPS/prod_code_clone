__author__ = 'johnm'

from ivetl.celery import app
from ivetl.pipelines.task import Task


@app.task
class InsertCustomArticleDataIntoCassandra(Task):
    pipeline_name = "custom_article_data"

    def run_task(self, publisher_id, job_id, work_folder, tlogger, task_args):
        print("Running insert for %s" % publisher_id)
        self.pipeline_ended(publisher_id, self.pipeline_name, job_id)
        return {}