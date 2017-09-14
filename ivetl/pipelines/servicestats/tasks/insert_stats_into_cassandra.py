import json
from dateutil.parser import parse
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import ServiceResponseTime, ServiceResponseCode
from ivetl import utils
from ivetl.common import common


@app.task
class InsertStatsIntoCassandraTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']
        to_date = self.from_json_date(task_args['to_date'])

        total_count = 0
        for file in files:
            total_count += utils.file_len(file)

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)
        count = 0

        for file in files:
            with open(file, encoding='utf-8') as stats_file:
                for line in stats_file:
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    if common.DEBUG_QUICKLY:
                        if count > 10:
                            continue

                    if line:
                        try:
                            stat_json = json.loads(line)
                        except ValueError:
                            tlogger.info('Bad line of JSON, skipping: %s' % line)
                            continue

                        duration_dict = stat_json['Duration']
                        ServiceResponseTime.objects(
                            publisher_id=publisher_id,
                            name=stat_json.get('Name'),
                            from_date=parse(stat_json.get('From')),
                            until_date=parse(stat_json.get('Until')),
                        ).update(
                            sample=stat_json.get('Sample'),
                            units=duration_dict.get('Units'),
                            mean=duration_dict.get('Mean'),
                            standard_deviation=duration_dict.get('StdDev'),
                            variance=duration_dict.get('Variance'),
                            minimum=duration_dict.get('Minimum'),
                            maximum=duration_dict.get('Maximum'),
                            percentile_25=duration_dict.get('Percentile25'),
                            percentile_50=duration_dict.get('Percentile50'),
                            percentile_75=duration_dict.get('Percentile75'),
                            percentile_95=duration_dict.get('Percentile95'),
                            percentile_99=duration_dict.get('Percentile99')
                        )

                        for status_code, count in stat_json['Status'].items():
                            ServiceResponseCode.objects(
                                publisher_id=publisher_id,
                                name=stat_json.get('Name'),
                                from_date=parse(stat_json.get('From')),
                                until_date=parse(stat_json.get('Until')),
                                status_code=status_code,
                            ).update(
                                sample=stat_json.get('Sample'),
                                count=count,
                            )

        utils.update_high_water(product_id, pipeline_id, publisher_id, to_date)

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, tlogger, show_alerts=task_args['show_alerts'])

        task_args['count'] = total_count

        return task_args
