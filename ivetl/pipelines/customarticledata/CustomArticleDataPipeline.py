import os
import datetime
from celery import chain
from ivetl.celery import app
from ivetl.common import common
from ivetl.pipelines.pipeline import Pipeline
from ivetl.pipelines.customarticledata import tasks
from ivetl.pipelines.publishedarticles import tasks as published_articles_tasks
from ivetl.models import Publisher_Metadata


@app.task
class CustomArticleDataPipeline(Pipeline):
    pipeline_name = 'custom_article_data'

    # 1. Pipeline - setup job and iterate over pubs that have non-empty directories.
    # 2. GetIncomingFiles - move the files across into work folder.
    # 3. ValidateFile - run through each file, checking for a variety of errors. If found, exit.
    # 4. InsertArticleData - insert non-overlapping data into pub_articles and overlapping into _values.
    # 5. ResolveArticleData - decide which data to promote from _values into pub_articles, and do the insert.

    def run(self, publisher_id_list=[], product_id=None, preserve_incoming_files=False, alt_incoming_dir=None):
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

            publisher_dir = self.get_or_create_incoming_dir_for_publisher(base_incoming_dir, publisher.publisher_id)
            if os.path.isdir(publisher_dir):

                # grab all files from the directory
                files = [f for f in os.listdir(publisher_dir) if os.path.isfile(os.path.join(publisher_dir, f))]

                # remove any hidden files, in particular .DS_Store
                files = [f for f in files if not f.startswith('.')]

                if files:

                    # create work folder, signal the start of the pipeline
                    work_folder = self.get_work_folder(today_label, publisher.publisher_id, job_id)
                    self.on_pipeline_started(publisher.publisher_id, job_id, work_folder)

                    # construct the first task args with all of the standard bits + the list of files
                    task_args = {
                        'pipeline_name': self.pipeline_name,
                        'publisher_id': publisher.publisher_id,
                        'work_folder': work_folder,
                        'job_id': job_id,
                        'uploaded_files': [os.path.join(publisher_dir, f) for f in files],
                        'preserve_incoming_files': preserve_incoming_files
                    }

                    # send alert email that we're processing for this publisher
                    subject = "%s - %s - Processing started for: %s" % (self.pipeline_name, today_label, publisher_dir)
                    text = "Processing files for " + publisher_dir
                    common.send_email(subject, text)

                    # and run the pipeline!
                    chain(
                        tasks.GetArticleDataFiles.s(task_args) |
                        tasks.ValidateArticleDataFiles.s() |
                        tasks.InsertCustomArticleDataIntoCassandra.s() |
                        published_articles_tasks.ResolvePublishedArticlesData.s()
                    ).delay()
