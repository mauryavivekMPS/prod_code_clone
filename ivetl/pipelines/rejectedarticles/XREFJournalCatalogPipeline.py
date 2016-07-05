from celery import chain
from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.models import Publisher_Metadata
from ivetl.pipelines.rejectedarticles import tasks


@app.task
class XREFJournalCatalogPipeline(Pipeline):

    def run(self, publisher_id_list=[], product_id=None, job_id=None, input_file=None, initiating_user_email=None):
        pipeline_id = "update_manuscripts"

        now, today_label, job_id = self.generate_job_id()

        if publisher_id_list:
            publishers = Publisher_Metadata.objects.filter(publisher_id__in=publisher_id_list)
        else:
            publishers = Publisher_Metadata.objects.filter(demo=False)  # default to production pubs

        publishers = [p for p in publishers if product_id in p.supported_products]

        for pm in publishers:

            publisher_id = pm.publisher_id

            # pipelines are per publisher, so now that we have data, we start the pipeline work
            work_folder = self.get_work_folder(today_label, publisher_id, product_id, pipeline_id, job_id)
            self.on_pipeline_started(publisher_id, product_id, pipeline_id, job_id, work_folder, initiating_user_email=initiating_user_email, total_task_count=1, current_task_count=0)

            task_args = {
                'publisher_id': publisher_id,
                'product_id': product_id,
                'pipeline_id': pipeline_id,
                'work_folder': work_folder,
                'job_id': job_id,
                'input_file': input_file,
            }

            chain(
                tasks.UpdateManuscriptsInCassandraTask(task_args)
            ).delay()
