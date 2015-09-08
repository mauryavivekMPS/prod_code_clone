__author__ = 'nmehta, johnm'

import datetime
from dateutil.relativedelta import relativedelta
from celery import chain
from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.models import Publisher_Metadata
from ivetl.pipelines.publishedarticles import tasks


@app.task
class UpdatePublishedArticlesPipeline(Pipeline):
    pipeline_name = "published_articles"
    PUB_START_DATE = datetime.date(2010, 1, 1)
    PUB_OVERLAP_MONTHS = 2

    def run(self, publisher_id_list=[], reprocess_all=False, articles_per_page=1000, max_articles_to_process=None):

        d = datetime.datetime.today()
        today = d.strftime('%Y%m%d')
        time = d.strftime('%H%M%S%f')
        job_id = today + "_" + time

        publishers_metadata = Publisher_Metadata.objects.all()

        if publisher_id_list:
            publishers_metadata = publishers_metadata.filter(publisher_id__in=publisher_id_list)

        for pm in publishers_metadata:

            publisher_id = pm.publisher_id
            issns = pm.published_articles_issns_to_lookup

            if reprocess_all:
                start_publication_date = self.PUB_START_DATE
            else:
                start_publication_date = pm.published_articles_last_updated - relativedelta(months=self.PUB_OVERLAP_MONTHS)

            # pipelines are per publisher, so now that we have data, we start the pipeline work
            work_folder = self.get_work_folder(today, publisher_id, job_id)
            self.on_pipeline_started(publisher_id, job_id, work_folder)

            task_args = {
                'pipeline_name': self.pipeline_name,
                'publisher_id': publisher_id,
                'work_folder': work_folder,
                'job_id': job_id,
                tasks.GetPublishedArticlesTask.ISSNS: issns,
                tasks.GetPublishedArticlesTask.START_PUB_DATE: start_publication_date,
                'articles_per_page': articles_per_page,
                'max_articles_to_process': max_articles_to_process,
            }

            if pm.hw_addl_metadata_available:
                chain(
                    tasks.GetPublishedArticlesTask.s(task_args) |
                    tasks.ScopusIdLookupTask.s() |
                    tasks.HWMetadataLookupTask.s() |
                    tasks.InsertPublishedArticlesIntoCassandra.s() |
                    tasks.ResolvePublishedArticlesData.s()
                ).delay()
            else:
                chain(
                    tasks.GetPublishedArticlesTask.s(task_args) |
                    tasks.ScopusIdLookupTask.s() |
                    tasks.InsertPublishedArticlesIntoCassandra.s() |
                    tasks.ResolvePublishedArticlesData.s()
                ).delay()