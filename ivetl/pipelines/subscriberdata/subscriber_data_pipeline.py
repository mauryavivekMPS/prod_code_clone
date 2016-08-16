from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.common import common


@app.task
class SubscribersAndSubscriptionsPipeline(Pipeline):

    OVERLAPPING_FIELDS = [
        ('firstname', 'First Name'),
        ('lastname', 'Last Name'),
        ('inst_name', 'Institution Name'),
        ('user_phone', 'Phone'),
        ('user_fax', 'Fax'),
        ('user_email', 'Email Address'),
        ('user_address', 'Address #2'),
        ('address_2', 'Title'),
        ('title', 'Affiliation'),
        ('affiliation', 'RingGold Id'),
        ('ringgold_id', 'Sales Agent'),
        ('sales_agent', 'Memo'),
        ('memo', 'Tier'),
        ('tier', 'Consortium'),
        ('consortium', 'Start Date'),
        ('start_date', 'Country'),
        ('country', 'Region'),
        ('region', 'Contact'),
        ('contact', 'Institution Alternate Name'),
        ('institution_alternate_name', 'Institution Alternate Identifier'),
        ('institution_alternate_identifier', 'Memo'),
        ('custom1', 'Custom #1'),
        ('custom2', 'Custom #2'),
        ('custom3', 'Custom #3'),

    ]

    OVERLAPPING_DATETIMES = [
        'start_date',
    ]

    def run(self, publisher_id_list=[], product_id=None, job_id=None, initiating_user_email=None):
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
        }

        self.chain_tasks(pipeline_id, task_args)
