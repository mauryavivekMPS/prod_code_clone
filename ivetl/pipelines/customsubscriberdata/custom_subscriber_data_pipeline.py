import os
from ivetl.celery import app
from ivetl.common import common
from ivetl.pipelines.pipeline import Pipeline
from ivetl.models import PublisherMetadata


@app.task
class CustomSubscriberDataPipeline(Pipeline):

    CUSTOM_FIELD_NAME_TO_SCHEMA_NAME = {
        'membership_no': 'MEMBERSHIP_NUMBER',
        'firstname': 'FIRST_NAME',
        'lastname': 'LAST_NAME',
        'inst_name': 'INSTITUTION_NAME',
        'user_phone': 'PHONE',
        'user_fax': 'FAX',
        'user_email': 'EMAIL',
        'user_address': 'ADDRESS',
        'address_2': 'ADDRESS_2',
        'title': 'TITLE',
        'affiliation': 'AFFILIATION',
        'ringgold_id': 'RINGOLD_ID',
        'sales_agent': 'SALES_AGENT',
        'tier': 'TIER',
        'consortium': 'CONSORTIUM',
        'start_date': 'START_DATE',
        'country': 'COUNTRY',
        'region': 'REGION',
        'contact': 'CONTACT',
        'institution_alternate_name': 'INSTITUTION_ALTERNATE_NAME',
        'institution_alternate_identifier': 'INSTITUTION_ALTERNATE_IDENTIFIER',
        'memo': 'MEMO',
        'custom1': 'CUSTOM_1',
        'custom2': 'CUSTOM_2',
        'custom3': 'CUSTOM_3',
    }

    def run(self, publisher_id_list=[], product_id=None, job_id=None, preserve_incoming_files=False, alt_incoming_dir=None, files=[], initiating_user_email=None, send_alerts=False):
        pipeline_id = 'custom_subscriber_data'
        now, today_label, job_id = self.generate_job_id()

        if publisher_id_list:
            publishers = PublisherMetadata.objects.filter(publisher_id__in=publisher_id_list)
        else:
            publishers = PublisherMetadata.objects.filter(demo=False)  # default to production pubs

        publishers = [p for p in publishers if product_id in p.supported_products]

        # figure out which publisher has a non-empty incoming dir
        for publisher in publishers:

            if not files:
                if alt_incoming_dir:
                    base_incoming_dir = alt_incoming_dir
                else:
                    base_incoming_dir = common.BASE_INCOMING_DIR

                publisher_dir = self.get_incoming_dir_for_publisher(base_incoming_dir, publisher.publisher_id, pipeline_id)

                # grab all files from the directory
                files = [f for f in os.listdir(publisher_dir) if os.path.isfile(os.path.join(publisher_dir, f))]

                # remove any hidden files, in particular .DS_Store
                files = [os.path.join(publisher_dir, f) for f in files if not f.startswith('.')]

            # create work folder, signal the start of the pipeline
            work_folder = self.get_work_folder(today_label, publisher.publisher_id, product_id, pipeline_id, job_id)
            self.on_pipeline_started(publisher.publisher_id, product_id, pipeline_id, job_id, work_folder, initiating_user_email=initiating_user_email)

            if files:
                # construct the first task args with all of the standard bits + the list of files
                task_args = {
                    'publisher_id': publisher.publisher_id,
                    'product_id': product_id,
                    'pipeline_id': pipeline_id,
                    'work_folder': work_folder,
                    'job_id': job_id,
                    'uploaded_files': files,
                    'preserve_incoming_files': preserve_incoming_files,
                    'send_alerts': send_alerts,
                }

                # and run the pipeline!
                Pipeline.chain_tasks(pipeline_id, task_args)

            else:
                self.pipeline_ended(publisher.publisher_id, product_id, pipeline_id, job_id, show_alerts=send_alerts)
