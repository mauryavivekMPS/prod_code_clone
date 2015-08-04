from __future__ import absolute_import

import datetime
from celery import chain

from ivetl.celery import app
from ivetl.common import common
from ivetl.common.BaseTask import BaseTask
from ivetl.articlecitations.GetScopusArticleCitationsTask import GetScopusArticleCitationsTask
from ivetl.articlecitations.InsertIntoCassandraDBTask import InsertIntoCassandraDBTask


@app.task
class ManualUpdateArticleCitationsTask(BaseTask):

    taskname = "ManualUpdateArticleCitations"
    vizor = common.AC

    def run(self, publisher, reprocesserrorsonly):

        d = datetime.datetime.today()
        today = d.strftime('%Y%m%d')
        time = d.strftime('%H%M%S%f')
        job_id = today + "_" + time

        wf = self.getWorkFolder(today, publisher, job_id)

        args = {}
        args[BaseTask.PUBLISHER_ID] = publisher
        args[BaseTask.WORK_FOLDER] = wf
        args[BaseTask.JOB_ID] = job_id
        args[GetScopusArticleCitationsTask.REPROCESS_ERRORS] = reprocesserrorsonly

        self.pipelineStarted(publisher, self.vizor, job_id, wf)

        chain(GetScopusArticleCitationsTask.s(args) |
              InsertIntoCassandraDBTask.s()).delay()







