import os
import datetime
from celery import chain
from ivetl.celery import app
from ivetl.common import common
from ivetl.pipelines.pipeline import Pipeline
from ivetl.pipelines.customarticledata import tasks
from ivetl.pipelines.publishedarticles import tasks as published_articles_tasks
from ivetl.models import Publisher_Metadata, Pipeline_Status


@app.task
class CustomArticleDataPipeline(Pipeline):

    # 1. Pipeline - setup job and iterate over pubs that have non-empty directories.
    # 2. GetIncomingFiles - move the files across into work folder.
    # 3. ValidateFile - run through each file, checking for a variety of errors. If found, exit.
    # 4. InsertArticleData - insert non-overlapping data into pub_articles and overlapping into _values.
    # 5. ResolveArticleData - decide which data to promote from _values into pub_articles, and do the insert.

    def run(self, publisher_id_list=[], product_id=None, job_id=None, preserve_incoming_files=False, alt_incoming_dir=None, files=[], initiating_user_email=None):
        pipeline_id = 'custom_article_data'
        now, today_label, job_id = self.generate_job_id()
        product = common.PRODUCT_BY_ID[product_id]

        if publisher_id_list:
            publishers = Publisher_Metadata.objects.filter(publisher_id__in=publisher_id_list)
        else:
            publishers = Publisher_Metadata.objects.all(demo=False)  # default to production pubs

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
                    tasks.GetArticleDataFiles.s(task_args) |
                    tasks.ValidateArticleDataFiles.s() |
                    tasks.InsertCustomArticleDataIntoCassandra.s() |
                    published_articles_tasks.ResolvePublishedArticlesData.s()
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
