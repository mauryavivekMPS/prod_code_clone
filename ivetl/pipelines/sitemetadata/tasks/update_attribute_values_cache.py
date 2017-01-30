import json
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import UptimeCheckMetadata, AttributeValues
from ivetl.alerts import CHECKS
from ivetl import utils


@app.task
class UpdateAttributeValuesCacheTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        all_checks = UptimeCheckMetadata.objects.filter(publisher_id=publisher_id)

        value_names = set()

        # look through all the alerts for uptime_check_metadata values
        for check_id, check in CHECKS.items():
            for f in check.get('filters', []):
                if f['table'] == 'uptime_check_metadata':
                    value_names.add(f['name'])

        total_count = utils.get_record_count_estimate(publisher_id, product_id, pipeline_id, self.short_name)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0

        for name in value_names:
            values = set()
            for check in all_checks:
                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                if check[name]:
                    values.add(check[name])

            AttributeValues.objects(
                publisher_id=publisher_id,
                name='uptime_check_metadata.' + name,
            ).update(
                values_json=json.dumps(list(values))
            )

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, tlogger, show_alerts=task_args['show_alerts'])

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, count)

        return task_args
