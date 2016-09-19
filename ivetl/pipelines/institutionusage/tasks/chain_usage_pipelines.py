from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl import utils

@app.task
class ChainUsagePipelinesTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        # mark this as ended first, to attempt to avoid race conditions
        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id)

        source_pipelines = [
            ('institutions', 'jr2_institution_usage'),
            ('institutions', 'jr3_institution_usage'),
            ('institutions', 'subscribers_and_subscriptions'),
            ('institutions', 'bundle_definitions'),
            ('institutions', 'subscription_pricing'),
        ]

        usage_pipelines = [
            ('institutions', 'update_institution_usage_deltas'),
            ('institutions', 'update_subscription_cost_per_use_deltas'),
        ]

        # if any of the source pipelines are running, then bail here and let them kick off the usage pipelines
        is_source_pipeline_running = False
        for source_product_id, source_pipeline_id in source_pipelines:
            if utils.is_pipeline_in_progress(publisher_id, source_product_id, source_pipeline_id):
                is_source_pipeline_running = True
                break

        # if either the usage pipelines are running, ask them to stop and restart, else just start them
        if not is_source_pipeline_running:
            for usage_product_id, usage_pipeline_id in usage_pipelines:
                if utils.is_pipeline_in_progress(publisher_id, usage_product_id, usage_pipeline_id):
                    pass
                    # TODO: fix this

        return task_args
