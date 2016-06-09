import os
import datetime
from celery import chain
from ivetl.celery import app
from ivetl.common import common
from ivetl.pipelines.pipeline import Pipeline
from ivetl.pipelines.institutionusage import tasks
from ivetl.models import Publisher_Metadata, Pipeline_Status


@app.task
class JR1InstitutionUsagePipeline(Pipeline):

    def run(self, publisher_id_list=[], product_id=None, job_id=None, preserve_incoming_files=False, alt_incoming_dir=None, files=[], initiating_user_email=None):
        pipeline_id = 'jr1_institution_usage'
        now, today_label, job_id = self.generate_job_id()
        product = common.PRODUCT_BY_ID[product_id]

        if publisher_id_list:
            publishers = Publisher_Metadata.objects.filter(publisher_id__in=publisher_id_list)
        else:
            publishers = Publisher_Metadata.objects.filter(demo=False)  # default to production pubs

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
            self.on_pipeline_started(publisher.publisher_id, product_id, pipeline_id, job_id, work_folder, initiating_user_email=initiating_user_email, total_task_count=4, current_task_count=0)

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
                }

                # and run the pipeline!
                chain(
                    tasks.GetJR1Files.s(task_args) |
                    tasks.ValidateJR1Files.s() |
                    tasks.InsertJR1IntoCassandra.s()
                ).delay()

            else:
                # note: this is annoyingly duplicated from task.pipeline_ended ... this should be factored better
                end_date = datetime.datetime.today()
                p = Pipeline_Status().objects.filter(publisher_id=publisher.publisher_id, product_id=product_id, pipeline_id=pipeline_id, job_id=job_id).first()
                if p is not None:
                    p.end_time = end_date
                    p.duration_seconds = (end_date - p.start_time).total_seconds()
                    p.status = self.PL_COMPLETED
                    p.updated = end_date
                    p.update()
