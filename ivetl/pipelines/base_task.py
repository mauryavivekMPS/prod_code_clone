import os
import json
import logging
import datetime
from dateutil.parser import parse
from celery import Task
from ivetl.common import common
from ivetl.connectors import TableauConnector
from ivetl.models import PublisherMetadata, PipelineStatus


class TaskParamsEncodingError(Exception):
    def __init__(self, type_error):
        message = "Task params must be JSON serializable: %s" % type_error
        super(TaskParamsEncodingError, self).__init__(message)


class BaseTask(Task):
    abstract = True

    PIPELINE_STATUS_STARTED = "started"
    PIPELINE_STATUS_IN_PROGRESS = "in-progress"
    PIPELINE_STATUS_COMPLETED = "completed"
    PIPELINE_STATUS_ERROR = "error"

    @property
    def short_name(self):
        return common.task_id_from_path(self.name)

    def get_work_folder(self, day, publisher_id, product_id, pipeline_id, job_id):
        return os.path.join(common.BASE_WORK_DIR, day, publisher_id, pipeline_id, job_id)

    def get_task_work_folder(self, work_folder):
        return os.path.join(work_folder, self.short_name)

    def setup_task(self, work_folder):
        task_work_folder = self.get_task_work_folder(work_folder)
        os.makedirs(task_work_folder, exist_ok=True)
        tlogger = self.init_task_logger(task_work_folder)
        return task_work_folder, tlogger

    def init_task_logger(self, task_work_folder):
        ti_logger = logging.getLogger(task_work_folder)
        fh = logging.FileHandler(task_work_folder + "/" + self.short_name + ".log", mode='w', encoding='utf-8')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ti_logger.addHandler(fh)
        ti_logger.propagate = False
        return ti_logger

    def get_task_logger(self, task_work_folder):
        return logging.getLogger(task_work_folder)

    def pipeline_ended(self, publisher_id, product_id, pipeline_id, job_id, send_notification_email=False, notification_count=None):
        end_date = datetime.datetime.today()

        pipeline = common.PIPELINE_BY_ID[pipeline_id]

        try:
            p = PipelineStatus.objects.get(
                publisher_id=publisher_id,
                product_id=product_id,
                pipeline_id=pipeline_id,
                job_id=job_id,
            )

            p.update(
                end_time=end_date,
                duration_seconds=(end_date - p.start_time).total_seconds(),
                status=self.PIPELINE_STATUS_COMPLETED,
                updated=end_date,
            )

            # only send email if the flag is set, it's a file input pipeline, and there is a valid pub email address
            if send_notification_email and pipeline.get('has_file_input'):
                if p.user_email:
                    subject = 'Impact Vizor (%s): Completed processing your %s file(s)' % (publisher_id, pipeline['user_facing_file_description'])
                    body = '<p>Impact Vizor has completed processing your %s file(s).</p>' % pipeline['user_facing_file_description']

                    if notification_count:
                        body += '<p>%s records were processed.<p>' % notification_count

                    body += '<p>Thank you,<br/>Impact Vizor Team</p>'

                    common.send_email(subject, body, to=p.user_email)

        except PipelineStatus.DoesNotExist:
            pass

        if (not common.IS_LOCAL) or (common.IS_LOCAL and common.PUBLISH_TO_TABLEAU_WHEN_LOCAL):
            publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)

            # update the data in tableau
            t = TableauConnector(
                username=common.TABLEAU_USERNAME,
                password=common.TABLEAU_PASSWORD,
                server=common.TABLEAU_SERVER
            )

            all_modified_datasources = set(common.TABLEAU_DATASOURCE_UPDATES.get((product_id, pipeline_id), []))
            for datasource_id in all_modified_datasources.intersection(publisher.all_datasources):
                t.refresh_data_source(publisher, datasource_id)

    def params_to_json(self, params):
        try:
            params_json = json.dumps(params)
        except TypeError as type_error:
            raise TaskParamsEncodingError(type_error)

        return params_json

    def to_json_date(self, d):
        if d:
            return d.strftime('%Y-%m-%d')
        else:
            return None

    def from_json_date(self, s):
        if s:
            return parse(s).date()
        else:
            return None

    def to_json_datetime(self, d):
        if d:
            return d.isoformat()
        else:
            return None

    def from_json_datetime(self, s):
        if s:
            return parse(s)
        else:
            return None
