from __future__ import absolute_import

import datetime
from dateutil.relativedelta import relativedelta
from celery import chain

from ivetl.celery import app
from ivetl.common import common
from ivetl.common.BaseTask import BaseTask
from ivetl.models.Metadata import Metadata
from ivetl.publishedarticles.GetPublishedArticlesTask import GetPublishedArticlesTask
from ivetl.publishedarticles.ScopusIdLookupTask import ScopusIdLookupTask
from ivetl.publishedarticles.HWMetadataLookupTask import HWMetadataLookupTask
from ivetl.publishedarticles.InsertIntoCassandraDBTask import InsertIntoCassandraDBTask


@app.task
class ScheduleUpdatePublishedArticlesTask(BaseTask):

    taskname = "ScheduleUpdatePublishedArticles"
    vizor = common.PA

    def run_task(self):

        d = datetime.datetime.today()
        today = d.strftime('%Y%m%d')
        time = d.strftime('%H%M%S%f')
        job_id = today + "_" + time

        publishers_metadata = Metadata.objects.all()

        for pm in publishers_metadata:

            publisher_id = pm.publisher_id
            issns = pm.issn.split(",")
            start_publication_date = pm.last_updated_date - relativedelta(months=common.PA_PUB_OVERLAP_MONTHS)

            args = {}
            args[BaseTask.PUBLISHER_ID] = publisher_id
            args[BaseTask.WORK_FOLDER] = self.getWorkFolder(today, publisher_id, job_id)
            args[BaseTask.JOB_ID] = job_id
            args[GetPublishedArticlesTask.ISSNS] = issns
            args[GetPublishedArticlesTask.START_PUB_DATE] = start_publication_date

            if pm.hw_addl_metadata_source:

                chain(GetPublishedArticlesTask.s(args) |
                      ScopusIdLookupTask.s() |
                      HWMetadataLookupTask.s() |
                      InsertIntoCassandraDBTask.s()).delay()

            else:

                chain(GetPublishedArticlesTask.s(args) |
                      ScopusIdLookupTask.s() |
                      InsertIntoCassandraDBTask.s()).delay()







