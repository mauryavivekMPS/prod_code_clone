import os
from ivetl.celery import app
from ivetl.common import common
from ivetl.pipelines.pipeline import Pipeline


@app.task
class CustomSubscriberDataPipeline(Pipeline):

    def run(self, publisher_id_list=[], product_id=None, job_id=None, preserve_incoming_files=False, alt_incoming_dir=None, files=[], initiating_user_email=None):
        pipeline_id = 'custom_subscriber_data'
        now, today_label, job_id = self.generate_job_id()

        # this pipeline operates on the global publisher ID
        pipeline = common.PIPELINE_BY_ID[pipeline_id]
        publisher_id = pipeline.get('single_publisher_id', 'hw')

        if not files:
            if alt_incoming_dir:
                base_incoming_dir = alt_incoming_dir
            else:
                base_incoming_dir = common.BASE_INCOMING_DIR

            publisher_dir = self.get_incoming_dir_for_publisher(base_incoming_dir, publisher_id, pipeline_id)

            # grab all files from the directory
            files = [f for f in os.listdir(publisher_dir) if os.path.isfile(os.path.join(publisher_dir, f))]

            # remove any hidden files, in particular .DS_Store
            files = [os.path.join(publisher_dir, f) for f in files if not f.startswith('.')]

        # create work folder, signal the start of the pipeline
        work_folder = self.get_work_folder(today_label, publisher_id, product_id, pipeline_id, job_id)
        self.on_pipeline_started(publisher_id, product_id, pipeline_id, job_id, work_folder, initiating_user_email=initiating_user_email)

        if files:
            # construct the first task args with all of the standard bits + the list of files
            task_args = {
                'publisher_id': publisher_id,
                'product_id': product_id,
                'pipeline_id': pipeline_id,
                'work_folder': work_folder,
                'job_id': job_id,
                'uploaded_files': files,
                'preserve_incoming_files': preserve_incoming_files,
            }

            # and run the pipeline!
            self.chain_tasks(pipeline_id, task_args)

        else:
            self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id)
