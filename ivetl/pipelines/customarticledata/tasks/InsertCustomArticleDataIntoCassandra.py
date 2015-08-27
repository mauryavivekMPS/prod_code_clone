__author__ = 'johnm'

from ivetl.celery import app
from ivetl.pipelines.task import Task


@app.task
class InsertCustomArticleDataIntoCassandra(Task):
    vizor = "published_articles"

    def run_task(self, publisher, job_id, workfolder, tlogger, args):
        self.pipeline_ended(publisher, self.vizor, job_id)
