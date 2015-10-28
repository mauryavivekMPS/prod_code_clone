import datetime
from celery import chain
from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.pipelines.articlecitations import tasks
from ivetl.models import Publisher_Metadata
from ivetl.common import common


@app.task
class UpdateArticleCitationsPipeline(Pipeline):
    pipeline_name = "article_citations"

    def run(self, publisher_id_list=[], product_id=None):

        now = datetime.datetime.now()
        today_label = now.strftime('%Y%m%d')
        job_id = now.strftime('%Y%m%d_%H%M%S%f')

        product = common.PRODUCT_BY_ID[product_id]

        # get the set of publishers to work on
        if publisher_id_list and len(publisher_id_list):
            publishers = Publisher_Metadata.filter(publisher_id__in=publisher_id_list)
        else:
            publishers = Publisher_Metadata.objects.all()

        # figure out which publisher has a non-empty incoming dir
        for publisher in publishers:

            if product['cohort'] and not publisher.is_cohort:
                continue
            if not product['cohort'] and publisher.is_cohort:
                continue

            # create work folder, signal the start of the pipeline
            work_folder = self.get_work_folder(today_label, publisher.publisher_id, job_id)
            self.on_pipeline_started(publisher.publisher_id, job_id, work_folder)

            # construct the first task args with all of the standard bits + the list of files
            task_args = {
                'pipeline_name': self.pipeline_name,
                'publisher_id': publisher.publisher_id,
                'work_folder': work_folder,
                'job_id': job_id,
                tasks.GetScopusArticleCitations.REPROCESS_ERRORS: False,
                'product_id': product_id
            }

            if publisher.is_cohort:
                chain(
                    tasks.GetScopusArticleCitations.s(task_args) |
                    tasks.InsertScopusIntoCassandra.s() |
                    tasks.InsertCohortOwnerCitationsTask.s()
                ).delay()
            elif publisher.crossref_username is not None and publisher.crossref_password is not None:
                chain(
                    tasks.GetScopusArticleCitations.s(task_args) |
                    tasks.InsertScopusIntoCassandra.s() |
                    tasks.UpdateArticleCitationsWithCrossref.s()
                ).delay()
            else:
                chain(
                    tasks.GetScopusArticleCitations.s(task_args) |
                    tasks.InsertScopusIntoCassandra.s()
                ).delay()
