import datetime
from celery import chain
from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.pipelines.rejectedarticles import tasks
from ivetl.pipelines.publishedarticles import tasks as published_articles_tasks
from ivetl.models import Publisher_Metadata


@app.task
class ReprocessRejectedArticlesPipeline(Pipeline):

    def run(self, publisher_id_list=[], product_id=None, job_id=None, initiating_user_email=None):
        pipeline_id = "reprocess_rejected_articles"

        now = datetime.datetime.now()
        today_label = now.strftime('%Y%m%d')
        job_id = now.strftime('%Y%m%d_%H%M%S%f')

        if publisher_id_list:
            publishers = Publisher_Metadata.objects.filter(publisher_id__in=publisher_id_list)
        else:
            publishers = Publisher_Metadata.objects.filter(demo=False)  # default to production pubs

        for publisher in publishers:

            # create work folder, signal the start of the pipeline
            work_folder = self.get_work_folder(today_label, publisher.publisher_id, product_id, pipeline_id, job_id)
            self.on_pipeline_started(publisher.publisher_id, product_id, pipeline_id, job_id, work_folder, initiating_user_email=initiating_user_email, total_task_count=8, current_task_count=0)

            # construct the first task args with all of the standard bits + the list of files
            task_args = {
                'pipeline_id': pipeline_id,
                'publisher_id': publisher.publisher_id,
                'product_id': product_id,
                'pipeline_id': pipeline_id,
                'work_folder': work_folder,
                'job_id': job_id,
            }

            chain(
                tasks.GetRejectedArticlesFromBenchpressTask.s(task_args) |
                tasks.XREFPublishedArticleSearchTask.s() |
                tasks.SelectPublishedArticleTask.s() |
                tasks.ScopusCitationLookupTask.s() |
                tasks.MendeleyLookupTask.s() |
                tasks.PrepareForDBInsertTask.s() |
                tasks.InsertIntoCassandraDBTask.s() |
                published_articles_tasks.CheckRejectedManuscriptTask.s()
            ).delay()
