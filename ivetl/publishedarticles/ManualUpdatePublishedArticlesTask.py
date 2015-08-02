from __future__ import absolute_import

import datetime
from celery import chain
from dateutil.relativedelta import relativedelta

from ivetl.celery import app
from ivetl.common import common
from ivetl.common.BaseTask import BaseTask
from ivetl.models.Metadata import Metadata
from ivetl.publishedarticles.GetPublishedArticlesTask import GetPublishedArticlesTask
from ivetl.publishedarticles.ScopusIdLookupTask import ScopusIdLookupTask
from ivetl.publishedarticles.HWMetadataLookupTask import HWMetadataLookupTask
from ivetl.publishedarticles.InsertIntoCassandraDBTask import InsertIntoCassandraDBTask


@app.task
class ManualUpdatePublishedArticlesTask(BaseTask):

    taskname = "ManualUpdatePublishedArticles"
    vizor = common.PA

    def run(self, publisher, reprocessall):

        d = datetime.datetime.today()
        today = d.strftime('%Y%m%d')
        time = d.strftime('%H%M%S%f')
        job_id = today + "_" + time

        pm = Metadata.objects.filter(publisher_id=publisher).first()

        issns = pm.issn.split(",")

        if reprocessall:
            start_publication_date = common.PA_PUB_START_DATE
        else:
            start_publication_date = pm.last_updated_date - relativedelta(months=common.PA_PUB_OVERLAP_MONTHS)

        args = {}
        args[BaseTask.PUBLISHER_ID] = publisher
        args[BaseTask.WORK_FOLDER] = self.getWorkFolder(today, publisher, job_id)
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








