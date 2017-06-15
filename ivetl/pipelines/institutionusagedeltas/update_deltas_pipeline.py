from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.models import PublisherMetadata


@app.task
class UpdateDeltasPipeline(Pipeline):

    def run(self, publisher_id_list=[], product_id=None, job_id=None, initiating_user_email=None, from_date=None, to_date=None, send_alerts=False):
        pipeline_id = "update_institution_usage_deltas"

        now, today_label, job_id = self.generate_job_id()

        if publisher_id_list:
            publishers = PublisherMetadata.objects.filter(publisher_id__in=publisher_id_list)
        else:
            publishers = PublisherMetadata.objects.filter(demo=False)  # default to production pubs

        publishers = [p for p in publishers if product_id in p.supported_products]

        for pm in publishers:

            publisher_id = pm.publisher_id

            # pipelines are per publisher, so now that we have data, we start the pipeline work
            work_folder = self.get_work_folder(today_label, publisher_id, product_id, pipeline_id, job_id)
            self.on_pipeline_started(publisher_id, product_id, pipeline_id, job_id, work_folder, initiating_user_email=initiating_user_email)

            task_args = {
                'publisher_id': publisher_id,
                'product_id': product_id,
                'pipeline_id': pipeline_id,
                'work_folder': work_folder,
                'job_id': job_id,
                'send_alerts': send_alerts,
                'from_date': self.to_json_date(from_date),
                'to_date': self.to_json_date(to_date),
            }

            Pipeline.chain_tasks(pipeline_id, task_args)
