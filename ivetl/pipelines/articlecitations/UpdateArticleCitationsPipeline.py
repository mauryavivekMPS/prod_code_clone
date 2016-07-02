from celery import chain
from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.pipelines.articlecitations import tasks
from ivetl.models import Publisher_Metadata
from ivetl.common import common


@app.task
class UpdateArticleCitationsPipeline(Pipeline):

    def run(self, publisher_id_list=[], product_id=None, job_id=None, initiating_user_email=None):
        pipeline_id = "article_citations"
        now, today_label, job_id = self.generate_job_id()

        product = common.PRODUCT_BY_ID[product_id]

        if publisher_id_list:
            publishers = Publisher_Metadata.objects.filter(publisher_id__in=publisher_id_list)
        else:
            publishers = Publisher_Metadata.objects.filter(demo=False)  # default to production pubs

        publishers = [p for p in publishers if product_id in p.supported_products]

        for publisher in publishers:

            # create work folder, signal the start of the pipeline
            work_folder = self.get_work_folder(today_label, publisher.publisher_id, product_id, pipeline_id, job_id)
            self.on_pipeline_started(publisher.publisher_id, product_id, pipeline_id, job_id, work_folder, initiating_user_email=initiating_user_email, total_task_count=3, current_task_count=0)

            # construct the first task args with all of the standard bits + the list of files
            task_args = {
                'pipeline_id': pipeline_id,
                'publisher_id': publisher.publisher_id,
                'product_id': product_id,
                'pipeline_id': pipeline_id,
                'work_folder': work_folder,
                'job_id': job_id,
                tasks.GetScopusArticleCitations.REPROCESS_ERRORS: False,
            }

            chain(
                tasks.GetScopusArticleCitations.s(task_args) |
                tasks.InsertScopusIntoCassandra.s() |
                tasks.UpdateArticleCitationsWithCrossref.s()
            ).delay()

