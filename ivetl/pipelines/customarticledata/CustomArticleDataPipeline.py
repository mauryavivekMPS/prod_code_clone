__author__ = 'johnm'

import os
import datetime
from celery import chain
from ivetl.celery import app
from ivetl.common import common
from ivetl.pipelines.pipeline import Pipeline
from ivetl.pipelines.customarticledata import tasks
from ivetl.models import Publisher_Metadata


@app.task
class CustomArticleDataPipeline(Pipeline):
    pipeline_name = 'custom_article_data'  # TODO: not sure what to do with this yet

    # 1. Pipeline - setup job and iterate over pubs that have non-empty directories.
    # 2. GetIncomingFiles - move the files across into work folder.
    # 3. ValidateFile - run through each file, checking for a variety of errors. If found, exit.
    # 4. InsertArticleData - insert non-overlapping data into pub_articles and overlapping into _values.
    # 5. ResolveArticleData - decide which data to promote from _values into pub_articles, and do the insert.

    def run(self, publisher_id_list=[]):
        now = datetime.datetime.now()
        today_label = now.strftime('%Y%m%d')
        job_id = now.strftime('%Y%m%d_%H%M%S%f')

        # get the set of publishers to work on
        if publisher_id_list:
            publishers = Publisher_Metadata.filter(publisher_id__in=publisher_id_list)
        else:
            publishers = Publisher_Metadata.objects.all()

        # figure out which publisher has a non-empty incoming dir
        for publisher in publishers:
            publisher_dir = os.path.join(common.BASE_INCOMING_DIR, publisher.publisher_id, self.pipeline_name)
            if os.path.isdir(publisher_dir):
                files = [f for f in os.listdir(publisher_dir) if os.path.isfile(os.path.join(publisher_dir, f))]
                if files:

                    # create work folder, signal the start of the pipeline
                    work_folder = self.get_work_folder(today_label, publisher.publisher_id, job_id)
                    self.pipeline_started(publisher.publisher_id, self.pipeline_name, job_id, work_folder)

                    print('pipeline work folder is: %s' % work_folder)

                    # send alert email that we're processing for this publisher
                    subject = "%s - %s - Processing started for: %s" % (self.pipeline_name, today_label, publisher_dir)
                    text = "Processing files for " + publisher_dir
                    common.send_email(subject, text)

                    # construct the first task args with all of the standard bits + the list of files
                    task_args = {
                        'publisher_id': publisher.publisher_id,
                        'work_folder': work_folder,
                        'job_id': job_id,
                        'uploaded_files': [os.path.join(publisher_dir, f) for f in files]
                    }

                    # and run the pipeline!
                    chain(
                        tasks.GetArticleDataFiles.s(task_args) |
                        tasks.ValidateArticleDataFiles.s() |
                        tasks.InsertCustomArticleDataIntoCassandra.s()
                    ).delay()

        #
        #
        #
        # for publisher_dir in os.listdir(common.BASE_INCOMING_DIR):
        #     if os.path.isdir(os.path.join(common.BASE_INCOMING_DIR, publisher_dir)):
        #
        #         srcpath = common.BASE_INCOMING_DIR + publisher_dir + "/" + common.RAT_DIR
        #         files = [f for f in os.listdir(srcpath) if os.path.isfile(os.path.join(srcpath, f))]
        #
        #         if len(files) > 0:
        #
        #
        # publishers_metadata = Publisher_Metadata.objects.all()
        #
        # if publishers:
        #     publishers_metadata = publishers_metadata.filter(publisher_id__in=publishers)
        #
        # for pm in publishers_metadata:
        #
        #     publisher_id = pm.publisher_id
        #     issns = pm.published_articles_issns_to_lookup
        #
        #     if reprocess_all:
        #         start_publication_date = common.PA_PUB_START_DATE
        #     else:
        #         start_publication_date = pm.published_articles_last_updated - relativedelta(months=common.PA_PUB_OVERLAP_MONTHS)
        #
        #     wf = self.get_work_folder(today, publisher_id, job_id)
        #
        #     args = {}
        #     args[self.PUBLISHER_ID] = publisher_id
        #     args[self.WORK_FOLDER] = wf
        #     args[self.JOB_ID] = job_id
        #     args[GetPublishedArticlesTask.ISSNS] = issns
        #     args[GetPublishedArticlesTask.START_PUB_DATE] = start_publication_date
        #
        #     self.pipeline_started(publisher_id, self.vizor, job_id, wf)
        #
        #     if pm.hw_addl_metadata_available:
        #         chain(GetPublishedArticlesTask.s(args) |
        #               ScopusIdLookupTask.s() |
        #               HWMetadataLookupTask.s() |
        #               InsertIntoCassandraDBTask.s()).delay()
        #     else:
        #         chain(GetPublishedArticlesTask.s(args) |
        #               ScopusIdLookupTask.s() |
        #               InsertIntoCassandraDBTask.s()).delay()
        #
        #
        # for publisher_dir in os.listdir(common.BASE_INCOMING_DIR):
        #
        #     if os.path.isdir(os.path.join(common.BASE_INCOMING_DIR, publisher_dir)):
        #
        #         srcpath = common.BASE_INCOMING_DIR + publisher_dir + "/" + common.RAT_DIR
        #         files = [f for f in os.listdir(srcpath) if os.path.isfile(os.path.join(srcpath, f))]
        #
        #         if len(files) > 0:
        #
                    # subject = "Rejected Article Tracker - " + today + " - Processing started for " + publisher_dir
                    # text = "Processing files for " + publisher_dir
                    # common.send_email(subject, text)
        #
        #             workfolder = common.BASE_WORK_DIR + today + "/" + publisher_dir + "/" + self.vizor + "/" + today + "_" + time
        #             dstworkpath = workfolder + "/" + self.taskname
        #             makedirs(dstworkpath, exist_ok=True)
        #
        #             tlogger = self.getTaskLogger(dstworkpath, self.taskname)
        #
        #             dstfiles = []
        #             for file in files:
        #
        #                 dstfile = dstworkpath + "/" + file
        #                 if os.path.exists(dstfile):
        #                     os.remove(dstfile)
        #
        #                 shutil.move(srcpath + "/" + file, dstfile)
        #                 dstfiles.append(dstfile)
        #
        #                 tlogger.info("Copied File:             " + file)
        #
        #             chain(ValidateInputFileTask.s(dstfiles, publisher_dir, today, workfolder) |
        #                   PrepareInputFileTask.s() |
        #                   XREFPublishedArticleSearchTask.s() |
        #                   SelectPublishedArticleTask.s() |
        #                   ScopusCitationLookupTask.s() |
        #                   PrepareForDBInsertTask.s() |
        #                   InsertIntoCassandraDBTask.s()).delay()
        #
        #


