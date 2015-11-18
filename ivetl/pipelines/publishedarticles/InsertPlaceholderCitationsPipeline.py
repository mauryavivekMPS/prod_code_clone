import datetime
from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.models import Publisher_Metadata
from ivetl.pipelines.publishedarticles import tasks
from ivetl.common import common


@app.task
class InsertPlaceholderCitationsPipeline(Pipeline):

    def run(self, publisher_id_list=[], product_id=None, reprocess_all=False, articles_per_page=1000, max_articles_to_process=None):
        pipeline_id = "placeholder_citations"

        d = datetime.datetime.today()
        today = d.strftime('%Y%m%d')
        time = d.strftime('%H%M%S%f')
        job_id = today + "_" + time

        product = common.PRODUCT_BY_ID[product_id]

        publishers_metadata = Publisher_Metadata.objects.all()

        if publisher_id_list:
            publishers_metadata = publishers_metadata.filter(publisher_id__in=publisher_id_list)

        for pm in publishers_metadata:

            publisher_id = pm.publisher_id

            # pipelines are per publisher, so now that we have data, we start the pipeline work
            work_folder = self.get_work_folder(today, publisher_id, product_id, pipeline_id, job_id)
            self.on_pipeline_started(publisher_id, product_id, pipeline_id, job_id, work_folder, total_task_count=1, current_task_count=0)

            task_args = {
                'publisher_id': publisher_id,
                'product_id': product_id,
                'pipeline_id': pipeline_id,
                'work_folder': work_folder,
                'job_id': job_id,
                'max_articles_to_process': max_articles_to_process,
            }

            tasks.InsertPlaceholderCitationsIntoCassandraTask.s(task_args).delay()
