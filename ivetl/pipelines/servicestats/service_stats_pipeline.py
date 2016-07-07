from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline


@app.task
class ServiceStatsPipeline(Pipeline):

    def run(self, publisher_id_list=[], product_id=None, job_id=None, initiating_user_email=None, from_date=None, to_date=None):
        pipeline_id = "service_stats"

        # this pipeline operates on the global publisher ID
        publisher_id = 'hw'

        now, today_label, job_id = self.generate_job_id()

        # create work folder, signal the start of the pipeline
        work_folder = self.get_work_folder(today_label, publisher_id, product_id, pipeline_id, job_id)
        self.on_pipeline_started(publisher_id, product_id, pipeline_id, job_id, work_folder, initiating_user_email=initiating_user_email, total_task_count=3, current_task_count=0)

        # construct the first task args with all of the standard bits + the list of files
        task_args = {
            'pipeline_id': pipeline_id,
            'publisher_id': publisher_id,
            'product_id': product_id,
            'work_folder': work_folder,
            'job_id': job_id,
            'from_date': self.to_json_date(from_date),
            'to_date': self.to_json_date(to_date),
        }

        self.chain_tasks(pipeline_id, task_args)
