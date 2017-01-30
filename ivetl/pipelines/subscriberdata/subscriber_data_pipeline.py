from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.common import common


@app.task
class SubscribersAndSubscriptionsPipeline(Pipeline):

    CUSTOMIZABLE_FIELD_NAMES = [
        'firstname',
        'lastname',
        'inst_name',
        'user_phone',
        'user_fax',
        'user_email',
        'address_2',
        'title',
        'affiliation',
        'ringgold_id',
        'sales_agent',
        'memo',
        'tier',
        'consortium',
        'start_date',
        'country',
        'region',
        'contact',
        'institution_alternate_name',
        'institution_alternate_identifier',
        'custom1',
        'custom2',
        'custom3',
    ]

    CUSTOMIZABLE_DATETIME_FIELD_NAMES = [
        'start_date',
    ]

    def run(self, publisher_id_list=[], product_id=None, job_id=None, initiating_user_email=None, send_alerts=False):
        pipeline_id = "subscribers_and_subscriptions"

        now, today_label, job_id = self.generate_job_id()

        # this pipeline operates on the global publisher ID
        pipeline = common.PIPELINE_BY_ID[pipeline_id]
        publisher_id = pipeline.get('single_publisher_id', 'hw')

        # create work folder, signal the start of the pipeline
        work_folder = self.get_work_folder(today_label, publisher_id, product_id, pipeline_id, job_id)
        self.on_pipeline_started(publisher_id, product_id, pipeline_id, job_id, work_folder, initiating_user_email=initiating_user_email)

        # construct the first task args with all of the standard bits + the list of files
        task_args = {
            'pipeline_id': pipeline_id,
            'publisher_id': publisher_id,
            'product_id': product_id,
            'work_folder': work_folder,
            'job_id': job_id,
            'send_alerts': send_alerts,
        }

        Pipeline.chain_tasks(pipeline_id, task_args)
