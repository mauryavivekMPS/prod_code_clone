import datetime
from dateutil.relativedelta import relativedelta
from celery import chain
from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.models import Publisher_Metadata
from ivetl.pipelines.publishedarticles import tasks


@app.task
class CheckRejectedManuscriptsPipeline(Pipeline):
    pipeline_name = "check_rejected_manuscripts"

    def run(self, publisher_id_list=[], product_id=None, max_articles_to_process=None):

        d = datetime.datetime.today()
        today = d.strftime('%Y%m%d')
        time = d.strftime('%H%M%S%f')
        job_id = today + "_" + time

        publishers_metadata = Publisher_Metadata.objects.all()

        if publisher_id_list:
            publishers_metadata = publishers_metadata.filter(publisher_id__in=publisher_id_list)

        for pm in publishers_metadata:

            publisher_id = pm.publisher_id

            # pipelines are per publisher, so now that we have data, we start the pipeline work
            work_folder = self.get_work_folder(today, publisher_id, job_id)
            self.on_pipeline_started(publisher_id, job_id, work_folder)

            task_args = {
                'pipeline_name': self.pipeline_name,
                'publisher_id': publisher_id,
                'product_id': product_id,
                'work_folder': work_folder,
                'job_id': job_id,
                'max_articles_to_process': max_articles_to_process,
            }

            chain(
                tasks.CheckRejectedManuscriptTask(task_args)
            ).delay()
