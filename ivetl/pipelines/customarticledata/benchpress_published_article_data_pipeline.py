import os
import datetime
from ivetl.celery import app
from ivetl.common import common
from ivetl.pipelines.pipeline import Pipeline
from ivetl.models import PublisherMetadata, PipelineStatus


@app.task
class BenchPressPublishedArticleDataPipeline(Pipeline):

    FOAM_FIELDS = [
        'article_type',
        'subject_category',
        'editor',
        'custom',
        'custom_2',
        'custom_3',
        'is_open_access',
    ]

    def run(self, publisher_id_list=[], product_id=None, job_id=None, initiating_user_email=None, from_date=None, to_date=None, send_alerts=False):
        pipeline_id = 'benchpress_published_article_data'
        if publisher_id_list:
            publishers = PublisherMetadata.objects.filter(publisher_id__in=publisher_id_list)
        else:
            # default to production pubs with benchpress support
            publishers = []
            for publisher in PublisherMetadata.objects.filter(demo=False):
                benchpress_journals = PublisherJournal.objects.filter(
                    publisher_id=publisher.publisher_id,
                    product_id='published_articles',
                    use_benchpress=True
                )
                if benchpress_journals.count():
                    publishers.append(publisher)

        publishers = [p for p in publishers if product_id in p.supported_products]

        for publisher in publishers:

            publisher_id = publisher.publisher_id

            params = {}
            today_label = ''

            if job_id:
                try:
                    ps = PipelineStatus.objects.get(
                        publisher_id=publisher_id,
                        product_id=product_id,
                        pipeline_id=pipeline_id,
                        job_id=job_id,
                    )

                    today_label = job_id.split("_")[0]

                    if ps.params_json:
                        params = json.loads(ps.params_json)

                        if params['from_date']:
                            from_date = parse(params['from_date'])

                        if params['to_date']:
                            to_date = parse(params['to_date'])

                except PipelineStatus.DoesNotExist:
                    pass

            if not job_id:
                now, today_label, job_id = self.generate_job_id()

                params = {
                    'from_date': from_date.strftime('%Y-%m-%d') if from_date else None,
                    'to_date': to_date.strftime('%Y-%m-%d') if to_date else None,
                }

            # create work folder, signal the start of the pipeline
            work_folder = self.get_work_folder(today_label, publisher_id, product_id, pipeline_id, job_id)
            self.on_pipeline_started(publisher_id, product_id, pipeline_id, job_id, work_folder, initiating_user_email=initiating_user_email, params=params)

            # construct the first task args with all of the standard bits + the list of files
            task_args = {
                'pipeline_id': pipeline_id,
                'publisher_id': publisher_id,
                'product_id': product_id,
                'work_folder': work_folder,
                'job_id': job_id,
                'from_date': self.to_json_date(from_date),
                'to_date': self.to_json_date(to_date),
                'send_alerts': send_alerts,
            }

            Pipeline.chain_tasks(pipeline_id, task_args)
