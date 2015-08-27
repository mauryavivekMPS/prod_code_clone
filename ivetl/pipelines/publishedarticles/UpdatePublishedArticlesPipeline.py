from __future__ import absolute_import

import datetime

from celery import chain
from dateutil.relativedelta import relativedelta

from ivetl.celery import app
from ivetl.common import common
from ivetl.pipelines.base import IvetlPipeline
from ivetl.models.PublisherMetadata import PublisherMetadata
from ivetl.pipelines.publishedarticles.tasks.GetPublishedArticlesTask import GetPublishedArticlesTask
from ivetl.pipelines.publishedarticles.tasks.ScopusIdLookupTask import ScopusIdLookupTask
from ivetl.pipelines.publishedarticles.tasks.HWMetadataLookupTask import HWMetadataLookupTask
from ivetl.pipelines.publishedarticles.tasks.InsertIntoCassandraDBTask import InsertIntoCassandraDBTask


@app.task
class UpdatePublishedArticlesPipeline(IvetlPipeline):
    vizor = common.PA

    def run(self, publishers=[], reprocess_all=False, articles_per_page=1000, max_articles_to_process=None):

        d = datetime.datetime.today()
        today = d.strftime('%Y%m%d')
        time = d.strftime('%H%M%S%f')
        job_id = today + "_" + time

        publishers_metadata = PublisherMetadata.objects.all()

        if publishers:
            publishers_metadata = publishers_metadata.filter(publisher_id__in=publishers)

        for pm in publishers_metadata:

            publisher_id = pm.publisher_id
            issns = pm.published_articles_issns_to_lookup

            if reprocess_all:
                start_publication_date = common.PA_PUB_START_DATE
            else:
                start_publication_date = pm.published_articles_last_updated - relativedelta(months=common.PA_PUB_OVERLAP_MONTHS)

            wf = self.get_work_folder(today, publisher_id, job_id)

            args = {}
            args[self.PUBLISHER_ID] = publisher_id
            args[self.WORK_FOLDER] = wf
            args[self.JOB_ID] = job_id
            args[GetPublishedArticlesTask.ISSNS] = issns
            args[GetPublishedArticlesTask.START_PUB_DATE] = start_publication_date

            self.pipeline_started(publisher_id, self.vizor, job_id, wf)

            if pm.hw_addl_metadata_available:
                chain(GetPublishedArticlesTask.s(args) |
                      ScopusIdLookupTask.s() |
                      HWMetadataLookupTask.s() |
                      InsertIntoCassandraDBTask.s()).delay()
            else:
                chain(GetPublishedArticlesTask.s(args) |
                      ScopusIdLookupTask.s() |
                      InsertIntoCassandraDBTask.s()).delay()
