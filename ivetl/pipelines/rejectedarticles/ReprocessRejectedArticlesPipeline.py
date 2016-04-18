import datetime
from celery import chain
from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.pipelines.rejectedarticles.tasks.GetRejectedArticlesFromBenchpressTask import GetRejectedArticlesFromBenchPressTask
from ivetl.pipelines.rejectedarticles.tasks.ParseBenchPressFileTask import ParseBenchPressFileTask
from ivetl.pipelines.rejectedarticles.tasks.XREFPublishedArticleSearchTask import XREFPublishedArticleSearchTask
from ivetl.pipelines.rejectedarticles.tasks.SelectPublishedArticleTask import SelectPublishedArticleTask
from ivetl.pipelines.rejectedarticles.tasks.ScopusCitationLookupTask import ScopusCitationLookupTask
from ivetl.pipelines.rejectedarticles.tasks.MendeleyLookupTask import MendeleyLookupTask
from ivetl.pipelines.rejectedarticles.tasks.PrepareForDBInsertTask import PrepareForDBInsertTask
from ivetl.pipelines.rejectedarticles.tasks.InsertIntoCassandraDBTask import InsertIntoCassandraDBTask
from ivetl.pipelines.publishedarticles.tasks.CheckRejectedManuscriptTask import CheckRejectedManuscriptTask
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
            self.on_pipeline_started(publisher.publisher_id, product_id, pipeline_id, job_id, work_folder, initiating_user_email=initiating_user_email, total_task_count=3, current_task_count=0)

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
                GetRejectedArticlesFromBenchPressTask.s(task_args) |
                ParseBenchPressFileTask.s() |
                XREFPublishedArticleSearchTask.s() |
                SelectPublishedArticleTask.s() |
                ScopusCitationLookupTask.s() |
                MendeleyLookupTask.s() |
                PrepareForDBInsertTask.s() |
                InsertIntoCassandraDBTask.s() |
                CheckRejectedManuscriptTask.s()
            ).delay()
