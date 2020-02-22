import os
import re
import json
import logging
import datetime
from dateutil.parser import parse
from celery import Task
from ivetl.common import common
from ivetl.connectors import TableauConnector
from ivetl.models import PublisherMetadata, PipelineStatus, TableauAlert, MonthlyMessage
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

    def pipeline_ended(self, publisher_id, product_id, pipeline_id, job_id, tlogger, send_notification_email=False, force_notification_email=False, run_monthly_job=False, show_alerts=False, task_args=None):
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
            if send_notification_email and (force_notification_email or pipeline.get('has_file_input')):
                if initiating_user_email:

                    if not re.match(r'[^@]+@[^@]+\.[^@]+', initiating_user_email):
                        tlogger.info('The initiating user email address "%s" is invalid, skipping email' % initiating_user_email)

                    else:

                        if pipeline.get('has_file_input'):
                            if task_args and task_args.get('input_files'):
                                files = task_args['input_files']
                                multiple_files = len(files) > 1
                            else:
                                files = []
                                multiple_files = False

                            subject = 'Impact Vizor (%s): Completed processing your %s file%s' % (
                                publisher_id,
                                pipeline['user_facing_file_description'],
                                's' if multiple_files else ''
                            )
                            body = '<p>Impact Vizor has completed processing your %s file%s.</p>' % (
                                pipeline['user_facing_file_description'],
                                's' if multiple_files else ''
                            )

                            if files:
                                for file in files:
                                    filename = file[file.rfind('/') + 1:]
                                    body += '<p style="margin-left:30px">Processed %s</p>' % filename

                        else:
                            subject = 'Impact Vizor (%s): Completed %s' % (publisher_id, pipeline.get('user_facing_pipeline_action', 'running task'))
                            body = '<p>Impact Vizor has completed %s.</p>' % pipeline.get('user_facing_pipeline_action', 'running the requested task')

                        body += '<p>Please note that it could take up to 30 minutes for the reports to display the processed changes.</p>'

                        body += '<p>Thank you,<br/>Impact Vizor Team</p>'

                        common.send_email(subject, body, to=initiating_user_email)

        except PipelineStatus.DoesNotExist:
            pass

        self.process_datasources(publisher_id, product_id, pipeline_id, tlogger)

        # if this is the first time the pipeline has finished, delete and re-add the workbook to update the
        all_time_number_of_jobs = PipelineStatus.objects.filter(
            publisher_id=publisher_id,
            product_id=product_id,
            pipeline_id=pipeline_id,
        ).count()

        if all_time_number_of_jobs < 2:
            self.re_add_workbooks_to_update_thumbnails(publisher_id, product_id, pipeline_id, tlogger)

        self.process_chains(publisher_id, product_id, pipeline_id, tlogger, initiating_user_email)
        self.process_alerts(publisher_id, product_id, pipeline_id, tlogger, run_monthly_job, show_alerts)

    def re_add_workbooks_to_update_thumbnails(self, publisher_id, product_id, pipeline_id, tlogger):
        if common.PUBLISH_TO_TABLEAU:
            tlogger.info('First time this pipeline has run, so re-adding workbooks for this product to update thumbnails')
            publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)

            # update the data in tableau
            t = TableauConnector(
                username=common.TABLEAU_USERNAME,
                password=common.TABLEAU_PASSWORD,
                server=common.TABLEAU_SERVER
            )

            product_group_ids_for_this_pipeline = []
            for group in common.PRODUCT_GROUPS:
                if product_id in group['products']:
                    product_group_ids_for_this_pipeline.append(group['id'])

            product_groups_to_update = set(product_group_ids_for_this_pipeline).intersection(publisher.supported_product_groups)

            # update all non-alert workbooks in the product groups of this pipeline - a little inefficient but oh well
            workbook_ids_to_update = set()
            for product_group_id in product_groups_to_update:
                for workbook_id in common.PRODUCT_GROUP_BY_ID[product_group_id]['tableau_workbooks']:
                    if not workbook_id.startswith('alert_'):
                        workbook_ids_to_update.add(workbook_id)

            existing_workbooks = t.list_workbooks(project_id=publisher.reports_project_id)
            existing_workbook_ids = set([common.TABLEAU_WORKBOOK_ID_BY_NAME[w['name']] for w in existing_workbooks if w['name'] in common.TABLEAU_WORKBOOK_ID_BY_NAME])
            workbook_tableau_id_lookup = {common.TABLEAU_WORKBOOK_ID_BY_NAME[d['name']]: d['id'] for d in existing_workbooks if d['name'] in common.TABLEAU_WORKBOOK_ID_BY_NAME}

            for workbook_id in existing_workbook_ids.intersection(workbook_ids_to_update):
                tlogger.info('Deleting %s' % workbook_id)
                t.delete_workbook_from_project(workbook_tableau_id_lookup[workbook_id])

            for workbook_id in workbook_ids_to_update:
                print('Adding %s' % workbook_id)
                t.add_workbook_to_project(publisher, workbook_id)

    def process_datasources(self, publisher_id, product_id, pipeline_id, tlogger):
        if common.PUBLISH_TO_TABLEAU:

            pipeline = common.PIPELINE_BY_ID[pipeline_id]

            if pipeline.get('single_publisher_pipeline') and publisher_id == pipeline.get('single_publisher_id', 'hw'):
                publishers = [p for p in PublisherMetadata.objects.all() if getattr(p, pipeline.get('update_publisher_datasource_if_attr_is_true', 'None'), False)]
                tlogger.info('Single publisher pipeline refreshing datasources for %s publishers' % len(publishers))
            else:
                publishers = [PublisherMetadata.objects.get(publisher_id=publisher_id)]

            for publisher in publishers:

                # update the data in tableau
                t = TableauConnector(
                    username=common.TABLEAU_USERNAME,
                    password=common.TABLEAU_PASSWORD,
                    server=common.TABLEAU_SERVER
                )

                all_modified_datasources = set(common.TABLEAU_DATASOURCE_UPDATES.get((product_id, pipeline_id), []))

                # when it's a single publisher pipeline we just have to update everything applicable
                if not (pipeline.get('single_publisher_pipeline') and publisher_id == pipeline.get('single_publisher_id', 'hw')):
                    all_datasources_to_update = all_modified_datasources.intersection(publisher.all_datasources)
                else:
                    all_datasources_to_update = all_modified_datasources

                pub_ds_to_update = set([
                    t._publisher_datasource_name(publisher, ds) for
                    ds in all_datasources_to_update
                ])

                tableau_ds_to_update = t.list_datasources_by_names(
                    pub_ds_to_update, publisher)

                ds_ids_to_update = [d['id'] for d in tableau_ds_to_update]

                for datasource_id in ds_ids_to_update:
                    loginfo = (publisher.publisher_id, datasource_id)
                    tlogger.info('Refreshing datasource: %s -> %s' % loginfo)
                    try:
                        t.refresh_data_source(datasource_id)
                    except:
                        tlogger.info('Refresh failed for %s, -> %s' % loginfo)
                        subject = 'Impact Vizor (%s): Refresh Failed' % (
                            publisher_id
                        )
                        body = '<p>Refresh failed: %s: %s </p>' % (
                            publisher.publisher_id,
                            datasource_id
                        )

                        body += ('<p>'
                            '<a href="https://help.tableau.com'
                            '/v2019.4/api/rest_api/en-us/REST/'
                            'rest_api_ref_datasources.htm'
                            '\#update_data_source_now"</a>'
                            'Tableau REST API Docs</p>'
                        '<p>POST /api/api-version/sites/$site-id'
                        '/datasources/$datasource-id/refresh</p>')

                        body += ('The action that failed is equivalent to'
                            ' selecting a data source using the '
                            'Tableau Server UI, and then '
                            'selecting Refresh Extracts from '
                            'the menu (also known as a "manual refresh").')

                        body += ('<p>An operator, developer, or support staff'
                            ' member should check the current status of '
                            'Tableau Server, diagnose the failure reason,'
                            ' and attempt to re-run the refresh manually.</p>')
                            
                        body += '<p>Thank you,<br/>Impact Vizor Team</p>'

                        common.send_email(subject, body, to=common.EMAIL_TO)
                        continue

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

    def process_alerts(self, publisher_id, product_id, pipeline_id, tlogger, run_monthly_job, show_alerts):
        if show_alerts or run_monthly_job:
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
                            run_alert = True
                        elif alert['type'] == 'threshold':
                            run_alert = alert['threshold_function'](publisher_id)

                        if run_alert:
                            tlogger.info('Running alert instance: %s' % alert_instance)

                            try:
                                monthly_message = MonthlyMessage.objects.get(
                                    product_id=product_id,
                                    pipeline_id=pipeline_id,
                                ).message
                            except MonthlyMessage.DoesNotExist:
                                monthly_message = None

                            tableau_alerts.process_alert(alert_instance, monthly_message=monthly_message)
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
