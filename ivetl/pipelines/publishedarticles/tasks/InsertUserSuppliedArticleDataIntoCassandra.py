__author__ = 'johnm'

from ivetl.celery import app
from ivetl.pipelines.chained_task import ChainedTask


@app.task
class InsertUserSuppliedArticleDataIntoCassandra(ChainedTask):
    vizor = "published_articles"

    def run_task(self, publisher, job_id, workfolder, tlogger, args):
        self.pipeline_ended(publisher, self.vizor, job_id)
