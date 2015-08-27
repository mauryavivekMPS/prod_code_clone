__author__ = 'johnm'

from ivetl.celery import app
from ivetl.pipelines.base import IvetlChainedTask


@app.task
class InsertUserSuppliedArticleDataIntoCassandra(IvetlChainedTask):
    vizor = "published_articles"

    def run_task(self, publisher, job_id, workfolder, tlogger, args):
        self.pipeline_ended(publisher, self.vizor, job_id)
