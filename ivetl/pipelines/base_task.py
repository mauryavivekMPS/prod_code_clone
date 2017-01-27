import os
import json
import logging
import datetime
from dateutil.parser import parse
from celery import Task
from ivetl.common import common
from ivetl.connectors import TableauConnector
from ivetl.models import PublisherMetadata, PipelineStatus, TableauAlert
from ivetl import tableau_alerts
from ivetl import utils


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

    def pipeline_ended(self, publisher_id, product_id, pipeline_id, job_id, tlogger, send_notification_email=False, notification_count=None, run_monthly_job=False):
        end_date = datetime.datetime.today()

        pipeline = common.PIPELINE_BY_ID[pipeline_id]
        initiating_user_email = None

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

            initiating_user_email = p.user_email

            # only send email if the flag is set, it's a file input pipeline, and there is a valid pub email address
            if send_notification_email and pipeline.get('has_file_input'):
                if initiating_user_email:
                    subject = 'Impact Vizor (%s): Completed processing your %s file(s)' % (publisher_id, pipeline['user_facing_file_description'])
                    body = '<p>Impact Vizor has completed processing your %s file(s).</p>' % pipeline['user_facing_file_description']

                    if notification_count:
                        body += '<p>%s records were processed.<p>' % notification_count

                    body += '<p>Thank you,<br/>Impact Vizor Team</p>'

                    common.send_email(subject, body, to=initiating_user_email)

        except PipelineStatus.DoesNotExist:
            pass

        self.process_datasources(publisher_id, product_id, pipeline_id, tlogger)
        self.process_chains(publisher_id, product_id, pipeline_id, tlogger, initiating_user_email)
        self.process_alerts(publisher_id, product_id, pipeline_id, tlogger, run_monthly_job)

    def process_datasources(self, publisher_id, product_id, pipeline_id, tlogger):
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
                tlogger.info('Refreshing datasource: %s' % datasource_id)
                t.refresh_data_source(publisher, datasource_id)

    def process_chains(self, publisher_id, product_id, pipeline_id, tlogger, initiating_user_email):
        for chain_id in common.CHAINS_BY_SOURCE_PIPELINE.get((product_id, pipeline_id), []):

            chain = common.CHAIN_BY_ID[chain_id]

            tlogger.info('Processing chain: %s' % chain['id'])

            # if any of the source pipelines are running, then bail here and let them kick off any dependents
            is_source_pipeline_running = False
            for source_product_id, source_pipeline_id in chain['source_pipelines']:
                most_recent_source_run = utils.get_most_recent_run(publisher_id, source_product_id, source_pipeline_id)
                if most_recent_source_run and most_recent_source_run.status == 'in-progress':
                    tlogger.info('Found other source pipelines running, will let them invoke the chain')
                    is_source_pipeline_running = True
                    break

            # if any of the dependent pipelines are running, ask them to stop and restart, else just start them
            if not is_source_pipeline_running:
                for dependent_product_id, dependent_pipeline_id in chain['dependent_pipelines']:
                    dependent_pipeline = common.PIPELINE_BY_ID[dependent_pipeline_id]

                    most_recent_dependent_run = utils.get_most_recent_run(publisher_id, dependent_product_id, dependent_pipeline_id)

                    if most_recent_dependent_run and most_recent_dependent_run.status == 'in-progress':
                        tlogger.info('Chained pipeline %s is running, stopping and restarting it' % dependent_pipeline_id)
                        most_recent_dependent_run.stop_instruction = 'stop-asap-and-restart'
                        most_recent_dependent_run.save()

                    else:
                        tlogger.info('Chained pipeline %s is not running, starting it' % dependent_pipeline_id)
                        pipeline_class = common.get_pipeline_class(dependent_pipeline)
                        pipeline_class.s(
                            publisher_id_list=[publisher_id],
                            product_id=dependent_product_id,
                            initiating_user_email=initiating_user_email,
                        ).delay()

    def process_alerts(self, publisher_id, product_id, pipeline_id, tlogger, run_monthly_job):
        for alert_id in tableau_alerts.ALERT_TEMPLATES_BY_SOURCE_PIPELINE.get((product_id, pipeline_id), []):

            alert = tableau_alerts.ALERT_TEMPLATES[alert_id]

            tlogger.info('Processing alert: %s' % alert_id)

            alert_instances = TableauAlert.objects.filter(
                alert_id=alert_id,
                publisher_id=publisher_id,
                archived=False,
            )

            for alert_instance in alert_instances:
                if alert_instance.enabled:

                    run_alert = False

                    if alert['type'] == 'scheduled':
                        if run_monthly_job:
                            run_alert = True
                    elif alert['type'] == 'threshold':
                        run_alert = alert['threshold_function'](publisher_id)

                    if run_alert:
                        tlogger.info('Running alert instance: %s' % alert_instance)
                        tableau_alerts.process_alert(alert_instance)
                    else:
                        tlogger.info('Skipping alert')

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
