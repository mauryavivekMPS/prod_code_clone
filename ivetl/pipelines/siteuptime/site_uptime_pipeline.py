import json
from dateutil.parser import parse
from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.models import Pipeline_Status
from ivetl.common import common


@app.task
class SiteUptimePipeline(Pipeline):

    def run(self, publisher_id_list=[], product_id=None, job_id=None, initiating_user_email=None, from_date=None, to_date=None, run_daily_uptime_alerts=False):
        pipeline_id = "site_uptime"

        # this pipeline operates on the global publisher ID
        pipeline = common.PIPELINE_BY_ID[pipeline_id]
        publisher_id = pipeline.get('single_publisher_id', 'hw')

        params = {}
        today_label = ''

        if job_id:
            try:
                ps = Pipeline_Status.objects.get(
                    publisher_id=publisher_id,
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

            except Pipeline_Status.DoesNotExist:
                pass

        if not job_id:
            now, today_label, job_id = self.generate_job_id()

            params = {
                'from_date': from_date.strftime('%Y-%m-%d') if from_date else None,
                'to_date': to_date.strftime('%Y-%m-%d') if to_date else None,
            }

        # create work folder, signal the start of the pipeline
        work_folder = self.get_work_folder(today_label, publisher_id, product_id, pipeline_id, job_id)
        self.on_pipeline_started(publisher_id, product_id, pipeline_id, job_id, work_folder, params=params, initiating_user_email=initiating_user_email, current_task_count=0)

        # construct the first task args with all of the standard bits + the list of files
        task_args = {
            'pipeline_id': pipeline_id,
            'publisher_id': publisher_id,
            'product_id': product_id,
            'work_folder': work_folder,
            'job_id': job_id,
            'from_date': from_date,
            'to_date': to_date,
            'run_daily_uptime_alerts': run_daily_uptime_alerts,
        }

        self.chain_tasks(pipeline_id, task_args)
