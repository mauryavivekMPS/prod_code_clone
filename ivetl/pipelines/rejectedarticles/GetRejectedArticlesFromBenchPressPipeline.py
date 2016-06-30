import json
import datetime
from dateutil.parser import parse
from celery import chain
from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.pipelines.rejectedarticles.tasks.GetRejectedArticlesFromBenchpressTask import GetRejectedArticlesFromBenchPressTask
from ivetl.pipelines.rejectedarticles.tasks.ParseBenchPressFileTask import ParseBenchPressFileTask
from ivetl.pipelines.rejectedarticles.tasks.XREFPublishedArticleSearchTask import XREFPublishedArticleSearchTask
from ivetl.pipelines.rejectedarticles.tasks.ScopusCitationLookupTask import ScopusCitationLookupTask
from ivetl.pipelines.rejectedarticles.tasks.MendeleyLookupTask import MendeleyLookupTask
from ivetl.pipelines.rejectedarticles.tasks.PrepareForDBInsertTask import PrepareForDBInsertTask
from ivetl.pipelines.rejectedarticles.tasks.InsertIntoCassandraDBTask import InsertIntoCassandraDBTask
from ivetl.pipelines.publishedarticles.tasks.CheckRejectedManuscriptTask import CheckRejectedManuscriptTask
from ivetl.models import Publisher_Metadata, Publisher_Journal, Pipeline_Status


@app.task
class GetRejectedArticlesFromBenchPressPipeline(Pipeline):

    def run(self, publisher_id_list=[], product_id=None, job_id=None, initiating_user_email=None, from_date=None, to_date=None):
        pipeline_id = "benchpress_rejected_articles"

        if publisher_id_list:
            publishers = Publisher_Metadata.objects.filter(publisher_id__in=publisher_id_list)
        else:
            # default to production pubs with benchpress support
            publishers = []
            for publisher in Publisher_Metadata.objects.filter(demo=False):
                benchpress_journals = Publisher_Journal.objects.filter(
                    publisher_id=publisher.publisher_id,
                    product_id='published_articles',
                    use_benchpress=True
                )
                if benchpress_journals.count():
                    publishers.append(publisher)

        publishers = [p for p in publishers if product_id in p.supported_products]

        now = datetime.datetime.now()
        start_at_scopus = False

        for publisher in publishers:

            if job_id:
                try:
                    ps = Pipeline_Status.objects.get(
                        publisher_id=publisher.publisher_id,
                        product_id=product_id,
                        pipeline_id=pipeline_id,
                        job_id=job_id,
                    )

                    job_id = ps.job_id
                    today_label = job_id.split("_")[0]

                    if ps.params_json:
                        params = json.loads(ps.params_json)

                        if params['from_date']:
                            from_date = parse(params['from_date'])

                        if params['to_date']:
                            to_date = parse(params['to_date'])

                    start_at_scopus = True

                except Pipeline_Status.DoesNotExist:
                    pass

            if not job_id:
                today_label = now.strftime('%Y%m%d')
                job_id = now.strftime('%Y%m%d_%H%M%S%f')

                params = {
                    'from_date': from_date.strftime('%Y-%m-%d') if from_date else None,
                    'to_date': to_date.strftime('%Y-%m-%d') if to_date else None,
                }

            # create work folder, signal the start of the pipeline
            work_folder = self.get_work_folder(today_label, publisher.publisher_id, product_id, pipeline_id, job_id)
            self.on_pipeline_started(publisher.publisher_id, product_id, pipeline_id, job_id, work_folder, params=params, initiating_user_email=initiating_user_email, total_task_count=9, current_task_count=0)

            # construct the first task args with all of the standard bits + the list of files
            task_args = {
                'pipeline_id': pipeline_id,
                'publisher_id': publisher.publisher_id,
                'product_id': product_id,
                'work_folder': work_folder,
                'job_id': job_id,
                'from_date': from_date,
                'to_date': to_date,
            }

            if start_at_scopus:
                chain(
                    ScopusCitationLookupTask.s(task_args) |
                    MendeleyLookupTask.s() |
                    PrepareForDBInsertTask.s() |
                    InsertIntoCassandraDBTask.s() |
                    CheckRejectedManuscriptTask.s()
                ).delay()
            else:
                chain(
                    GetRejectedArticlesFromBenchPressTask.s(task_args) |
                    ParseBenchPressFileTask.s() |
                    XREFPublishedArticleSearchTask.s() |
                    ScopusCitationLookupTask.s() |
                    MendeleyLookupTask.s() |
                    PrepareForDBInsertTask.s() |
                    InsertIntoCassandraDBTask.s() |
                    CheckRejectedManuscriptTask.s()
                ).delay()
