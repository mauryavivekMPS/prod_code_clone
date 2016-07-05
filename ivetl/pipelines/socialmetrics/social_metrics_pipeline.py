from celery import chain
from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.pipelines.socialmetrics import tasks


@app.task
class SocialMetricsPipeline(Pipeline):

    def run(self, publisher_id_list=[], product_id=None, job_id=None, initiating_user_email=None):
        pipeline_id = "social_metrics"

        now, today_label, job_id = self.generate_job_id()

        # this pipeline operates on the global publisher ID
        publisher_id = 'hw'

        # create work folder, signal the start of the pipeline
        work_folder = self.get_work_folder(today_label, publisher_id, product_id, pipeline_id, job_id)
        self.on_pipeline_started(publisher_id, product_id, pipeline_id, job_id, work_folder, initiating_user_email=initiating_user_email, total_task_count=4, current_task_count=0)

        # construct the first task args with all of the standard bits + the list of files
        task_args = {
            'pipeline_id': pipeline_id,
            'publisher_id': publisher_id,
            'product_id': product_id,
            'work_folder': work_folder,
            'job_id': job_id,
        }

        chain(
            tasks.LoadAltmetricsDataTask.s(task_args) |
            tasks.LoadF1000DataTask.s()
        ).delay()
