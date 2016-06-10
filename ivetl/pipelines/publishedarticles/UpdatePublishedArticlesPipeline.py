import datetime
from celery import chain
from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.models import Publisher_Metadata, Publisher_Journal
from ivetl.pipelines.publishedarticles import tasks
from ivetl.common import common


@app.task
class UpdatePublishedArticlesPipeline(Pipeline):
    PUB_START_DATE = datetime.date(2010, 1, 1)
    COHORT_PUB_START_DATE = datetime.date(2013, 1, 1)
    PUB_OVERLAP_MONTHS = 2

    def run(self, publisher_id_list=[], product_id=None, job_id=None, reprocess_all=False, articles_per_page=1000, max_articles_to_process=None, initiating_user_email=None, run_monthly_job=False):
        pipeline_id = "published_articles"

        d = datetime.datetime.today()
        today = d.strftime('%Y%m%d')
        time = d.strftime('%H%M%S%f')
        job_id = today + "_" + time

        product = common.PRODUCT_BY_ID[product_id]

        if publisher_id_list:
            publishers = Publisher_Metadata.objects.filter(publisher_id__in=publisher_id_list)
        else:
            publishers = Publisher_Metadata.objects.filter(demo=False)  # default to production pubs

        publishers = [p for p in publishers if product_id in p.supported_products]

        for pm in publishers:

            publisher_id = pm.publisher_id

            # get ISSNs by product to deal with cohort or not
            issns = [j.print_issn for j in Publisher_Journal.objects.filter(publisher_id=publisher_id, product_id=product_id)]
            issns.extend([j.electronic_issn for j in Publisher_Journal.objects.filter(publisher_id=publisher_id, product_id=product_id)])

            if product['cohort']:
                start_publication_date = self.COHORT_PUB_START_DATE
            else:
                start_publication_date = self.PUB_START_DATE

            # pipelines are per publisher, so now that we have data, we start the pipeline work
            work_folder = self.get_work_folder(today, publisher_id, product_id, pipeline_id, job_id)
            self.on_pipeline_started(publisher_id, product_id, pipeline_id, job_id, work_folder, initiating_user_email=initiating_user_email, total_task_count=6, current_task_count=0)

            task_args = {
                'product_id': product_id,
                'publisher_id': publisher_id,
                'pipeline_id': pipeline_id,
                'work_folder': work_folder,
                'job_id': job_id,
                tasks.GetPublishedArticlesTask.ISSNS: issns,
                tasks.GetPublishedArticlesTask.START_PUB_DATE: start_publication_date,
                'articles_per_page': articles_per_page,
                'max_articles_to_process': max_articles_to_process,
                'run_monthly_job': run_monthly_job,
            }

            chain(
                tasks.GetPublishedArticlesTask.s(task_args) |
                tasks.ScopusIdLookupTask.s() |
                tasks.GetHighWireMetadataTask.s() |
                tasks.MendeleyLookupTask.s() |
                tasks.InsertPublishedArticlesIntoCassandra.s() |
                tasks.ResolvePublishedArticlesData.s() |
                tasks.UpdateAttributeValuesCacheTask.s() |
                tasks.ResolveArticleUsageData.s() |
                tasks.CheckRejectedManuscriptTask.s()
            ).delay()
