__author__ = 'nmehta'

import datetime
from celery import chain
from ivetl.celery import app
from ivetl.common import common
from ivetl.pipelines.articlecitations.tasks.GetScopusArticleCitationsTask import GetScopusArticleCitationsTask
from ivetl.pipelines.articlecitations.tasks.InsertIntoCassandraDBTask import InsertIntoCassandraDBTask
from ivetl.models.PublisherMetadata import PublisherMetadata
from ivetl.pipelines.pipeline import Pipeline


@app.task
class UpdateArticleCitationsPipeline(Pipeline):
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

            wf = self.getWorkFolder(today, publisher_id, job_id)

            args = {}
            args[BaseTask.PUBLISHER_ID] = publisher_id
            args[BaseTask.WORK_FOLDER] = wf
            args[BaseTask.JOB_ID] = job_id
            args[GetScopusArticleCitationsTask.REPROCESS_ERRORS] = False

            self.pipelineStarted(publisher_id, self.vizor, job_id, wf)

            chain(GetScopusArticleCitationsTask.s(args) |
                  InsertIntoCassandraDBTask.s()).delay()







