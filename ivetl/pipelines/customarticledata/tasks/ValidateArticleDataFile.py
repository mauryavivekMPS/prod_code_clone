__author__ = 'johnm'

from ivetl.celery import app
from ivetl.pipelines.task import Task


@app.task
class ValidateArticleDataFile(Task):
    vizor = "published_articles"

    def run_task(self, publisher, job_id, workfolder, tlogger, args):
        pass
