import csv
import json
import codecs
from dateutil.parser import parse
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import Uptime_Check, System_Global


@app.task
class InsertIntoCassandra(Task):
    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        file = task_args['input_file']
        total_count = task_args['count']
        to_date = task_args['to_date']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0
        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                if count == 1:
                    continue

                check = json.loads(line[1])

                for stat in check['stats']:

                    Uptime_Check.objects(
                        publisher_id=publisher_id,
                        check_id=check['id'],
                        check_date=parse(stat['date']),
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
                        avg_response_ms=stat['avg_response_ms'],
                        total_up_sec=stat['total_up_sec'],
                        total_down_sec=stat['total_down_sec'],
                        total_unknown_sec=stat['total_unknown_sec'],
                    )

        # update high water mark
        System_Global.objects(name='last_uptime_day_processed').update(date_value=to_date)

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id)

        return {
            'count': count
        }
