import datetime
from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.models import PublisherMetadata, SystemGlobal


@app.task
class UpdateDeltasPipeline(Pipeline):

    def run(self, publisher_id_list=[], product_id=None, job_id=None, initiating_user_email=None, from_date=None, to_date=None, send_alerts=False):
        pipeline_id = "update_subscription_cost_per_use_deltas"

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

            now = datetime.datetime.now()

            earliest_date_value_global_name = publisher_id + '_institution_usage_stat_for_cost_earliest_date_value'
            earliest_date_dirty_global_name = publisher_id + '_institution_usage_stat_for_cost_earliest_date_dirty'

            if not from_date:
                try:
                    from_date = SystemGlobal.objects.get(name=earliest_date_value_global_name).date_value.date()
                except SystemGlobal.DoesNotExist:
                    from_date = datetime.date(2013, 1, 1)

            earliest_date_global = SystemGlobal.objects(name=earliest_date_value_global_name)
            earliest_date_global.update(date_value=from_date)

            SystemGlobal.objects(name=earliest_date_dirty_global_name).update(int_value=0)

            if not to_date:
                to_date = datetime.date(now.year, now.month, 1)

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
