import csv
import json
import codecs
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import UptimeCheckMetadata


@app.task
class InsertChecksIntoCassandraTask(Task):
    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        file = task_args['input_file']
        total_count = task_args['count']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0
        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                if count == 1:
                    continue

                check = json.loads(line[1])

                if check['drupal_launch_date']:
                    drupal_launch_date = self.from_json_date(check['drupal_launch_date'])
                else:
                    drupal_launch_date = None

                UptimeCheckMetadata.objects(
                    publisher_id=publisher_id,
                    check_id=check['id'],
                ).update(
                    check_type=check['check_type'],
                    check_name=check['name'],
                    check_url=check['hostname'] + check['type']['http']['url'],
                    pingdom_account=check['account'],
                    site_code=check['site_code'],
                    site_name=check['site_name'],
                    site_type=check['site_type'],
                    site_platform=check['site_platform'],
                    publisher_name=check['publisher_name'],
                    publisher_code=check['publisher_code'],
                    drupal_launch_date=drupal_launch_date,
                )

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, tlogger, show_alerts=task_args['show_alerts'])

        task_args['count'] = count
        return task_args
