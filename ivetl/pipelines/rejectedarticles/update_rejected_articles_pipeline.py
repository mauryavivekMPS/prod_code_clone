import os
import os.path
import datetime
from ivetl.common import common
from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.models import PublisherMetadata, PipelineStatus


@app.task
class UpdateRejectedArticlesPipeline(Pipeline):

    def run(self, publisher_id_list=[], product_id=None, job_id=None, preserve_incoming_files=False, alt_incoming_dir=None, files=[], initiating_user_email=None, send_alerts=False):
        pipeline_id = 'rejected_articles'

        now, today_label, job_id = self.generate_job_id()

        product = common.PRODUCT_BY_ID[product_id]

        if publisher_id_list:
            publishers = PublisherMetadata.objects.filter(publisher_id__in=publisher_id_list)
        else:
            publishers = PublisherMetadata.objects.filter(demo=False)  # default to production pubs

        publishers = [p for p in publishers if product_id in p.supported_products]

        # figure out which publisher has a non-empty incoming dir
        for publisher in publishers:

            if product['cohort']:
                continue

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
                # note: this is annoyingly duplicated from task.pipeline_ended ... this should be factored better
                end_date = datetime.datetime.today()
                p = PipelineStatus().objects.filter(publisher_id=publisher.publisher_id, product_id=product_id, pipeline_id=pipeline_id, job_id=job_id).first()
                if p is not None:
                    p.end_time = end_date
                    p.duration_seconds = (end_date - p.start_time).total_seconds()
                    p.status = self.PIPELINE_STATUS_COMPLETED
                    p.updated = end_date
                    p.update()
