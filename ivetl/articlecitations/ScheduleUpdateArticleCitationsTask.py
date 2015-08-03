from __future__ import absolute_import

import datetime
from celery import chain

from ivetl.celery import app
from ivetl.common import common
from ivetl.common.BaseTask import BaseTask
from ivetl.articlecitations.GetScopusArticleCitationsTask import GetScopusArticleCitationsTask
from ivetl.articlecitations.InsertIntoCassandraDBTask import InsertIntoCassandraDBTask
from ivetl.models.PublisherMetadata import PublisherMetadata


@app.task
class ScheduleUpdateArticleCitationsTask(BaseTask):

    taskname = "ScheduleUpdateArticleCitations"
    vizor = common.AC

    def run(self):

        d = datetime.datetime.today()
        today = d.strftime('%Y%m%d')
        time = d.strftime('%H%M%S%f')
        job_id = today + "_" + time

        publishers_metadata = PublisherMetadata.objects.all()

        for pm in publishers_metadata:

            publisher_id = pm.publisher_id

            args = {}
            args[BaseTask.PUBLISHER_ID] = publisher_id
            args[BaseTask.WORK_FOLDER] = self.getWorkFolder(today, publisher_id, job_id)
            args[BaseTask.JOB_ID] = job_id
            args[GetScopusArticleCitationsTask.REPROCESS_ERRORS] = False

            chain(GetScopusArticleCitationsTask.s(args) |
                  InsertIntoCassandraDBTask.s()).delay()







