__author__ = 'johnm'

from ivetl.celery import app
from ivetl.pipelines.base import IvetlChainedTask


@app.task
class ValidateArticleDataFile(IvetlChainedTask):
    vizor = "published_articles"

    def run_task(self, publisher, job_id, workfolder, tlogger, args):
        pass
