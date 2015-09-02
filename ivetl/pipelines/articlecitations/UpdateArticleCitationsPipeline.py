__author__ = 'nmehta'

import datetime
from celery import chain
from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.pipelines.articlecitations import tasks
from ivetl.models import Publisher_Metadata


@app.task
class UpdateArticleCitationsPipeline(Pipeline):
    pipeline_name = "article_citations"

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

            # create work folder, signal the start of the pipeline
            work_folder = self.get_work_folder(today_label, publisher.publisher_id, job_id)
            self.on_pipeline_started(publisher.publisher_id, job_id, work_folder)

            # construct the first task args with all of the standard bits + the list of files
            task_args = {
                'pipeline_name': self.pipeline_name,
                'publisher_id': publisher.publisher_id,
                'work_folder': work_folder,
                'job_id': job_id,
                tasks.GetScopusArticleCitationsTask.REPROCESS_ERRORS: False
            }

            chain(
                tasks.GetScopusArticleCitationsTask.s(task_args) |
                tasks.InsertIntoCassandraDBTask.s()
            ).delay()







