import os
import os.path
import datetime
from celery import chain
from ivetl.common import common
from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.pipelines.rejectedarticles import tasks
from ivetl.models import Publisher_Metadata, Pipeline_Status


@app.task
class UpdateRejectedArticlesPipeline(Pipeline):

    def run(self, publisher_id_list=[], product_id=None, preserve_incoming_files=False, alt_incoming_dir=None):
        pipeline_id = 'rejected_articles'

        now = datetime.datetime.now()
        today_label = now.strftime('%Y%m%d')
        job_id = now.strftime('%Y%m%d_%H%M%S%f')

        product = common.PRODUCT_BY_ID[product_id]

        # get the set of publishers to work on
        if publisher_id_list:
            publishers = Publisher_Metadata.filter(publisher_id__in=publisher_id_list)
        else:
            publishers = Publisher_Metadata.objects.all()

        if alt_incoming_dir:
            base_incoming_dir = alt_incoming_dir
        else:
            base_incoming_dir = common.BASE_INCOMING_DIR

        # figure out which publisher has a non-empty incoming dir
        for publisher in publishers:

            if product['cohort']:
                continue

            publisher_dir = self.get_or_create_incoming_dir_for_publisher(base_incoming_dir, publisher.publisher_id, pipeline_id)
            if os.path.isdir(publisher_dir):

                # grab all files from the directory
                files = [f for f in os.listdir(publisher_dir) if os.path.isfile(os.path.join(publisher_dir, f))]

                # remove any hidden files, in particular .DS_Store
                files = [f for f in files if not f.startswith('.')]

                # create work folder, signal the start of the pipeline
                work_folder = self.get_work_folder(today_label, publisher.publisher_id, product_id, pipeline_id, job_id)
                self.on_pipeline_started(publisher.publisher_id, product_id, pipeline_id, job_id, work_folder, total_task_count=8, current_task_count=0)

                if files:
                    # construct the first task args with all of the standard bits + the list of files
                    task_args = {
                        'publisher_id': publisher.publisher_id,
                        'product_id': product_id,
                        'pipeline_id': pipeline_id,
                        'work_folder': work_folder,
                        'job_id': job_id,
                        'uploaded_files': [os.path.join(publisher_dir, f) for f in files],
                        'preserve_incoming_files': preserve_incoming_files,
                    }

                    # send alert email that we're processing for this publisher
                    subject = "%s - %s - Processing started for: %s" % (pipeline_id, today_label, publisher_dir)
                    text = "Processing files for " + publisher_dir
                    common.send_email(subject, text)

                    # and run the pipeline!
                    chain(
                        tasks.GetRejectedArticlesDataFiles.s(task_args) |
                        tasks.ValidateInputFileTask.s() |
                        tasks.PrepareInputFileTask.s() |
                        tasks.XREFPublishedArticleSearchTask.s() |
                        tasks.SelectPublishedArticleTask.s() |
                        tasks.ScopusCitationLookupTask.s() |
                        tasks.PrepareForDBInsertTask.s() |
                        tasks.InsertIntoCassandraDBTask.s()
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
