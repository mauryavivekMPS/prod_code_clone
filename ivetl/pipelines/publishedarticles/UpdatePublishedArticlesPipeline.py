__author__ = 'nmehta, johnm'

import datetime
from dateutil.relativedelta import relativedelta
from celery import chain
from ivetl.celery import app
from ivetl.common import common
from ivetl.pipelines.base import IvetlPipeline
from ivetl.models.PublisherMetadata import PublisherMetadata
from ivetl.pipelines.publishedarticles.tasks.GetPublishedArticlesTask import GetPublishedArticlesTask
from ivetl.pipelines.publishedarticles.tasks.ScopusIdLookupTask import ScopusIdLookupTask
from ivetl.pipelines.publishedarticles.tasks.HWMetadataLookupTask import HWMetadataLookupTask
from ivetl.pipelines.publishedarticles.tasks.InsertPublishedArticlesIntoCassandra import InsertPublishedArticlesIntoCassandra


@app.task
class UpdatePublishedArticlesPipeline(IvetlPipeline):
    vizor = "published_articles"
    PUB_START_DATE = datetime.date(2010, 1, 1)
    PUB_OVERLAP_MONTHS = 2

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
                start_publication_date = self.PUB_START_DATE
            else:
                start_publication_date = pm.published_articles_last_updated - relativedelta(months=self.PUB_OVERLAP_MONTHS)

            wf = self.get_work_folder(today, publisher_id, job_id)

            args = {
                self.PUBLISHER_ID: publisher_id,
                self.WORK_FOLDER: wf,
                self.JOB_ID: job_id,
                GetPublishedArticlesTask.ISSNS: issns,
                GetPublishedArticlesTask.START_PUB_DATE: start_publication_date,
                'articles_per_page': articles_per_page,
                'max_articles_to_process': max_articles_to_process,
            }

            self.pipeline_started(publisher_id, self.vizor, job_id, wf)

            if pm.hw_addl_metadata_available:
                chain(GetPublishedArticlesTask.s(args) |
                      ScopusIdLookupTask.s() |
                      HWMetadataLookupTask.s() |
                      InsertPublishedArticlesIntoCassandra.s()).delay()
            else:
                chain(GetPublishedArticlesTask.s(args) |
                      ScopusIdLookupTask.s() |
                      InsertPublishedArticlesIntoCassandra.s()).delay()
