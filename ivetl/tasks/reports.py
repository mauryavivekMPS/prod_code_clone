import datetime
import logging
import traceback
from ivetl.common import common
from ivetl.models import PublisherMetadata, AuditLog, SingletonTaskStatus
from ivetl.connectors import TableauConnector
from ivetl.celery import app

log = logging.getLogger(__name__)


@app.task
def update_reports_for_publisher(publisher_id, initiating_user_id, include_initial_setup=False):
    publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)
    publisher.reports_setup_status = 'in-progress'
    publisher.save()

    try:
        t = TableauConnector(
            username=common.TABLEAU_USERNAME,
            password=common.TABLEAU_PASSWORD,
            server=common.TABLEAU_SERVER
        )

        if include_initial_setup:
            if publisher.demo:
                project_id, group_id, user_id = t.setup_account(publisher)
            else:
                project_id, group_id, user_id = t.setup_account(
                    publisher,
                    create_new_login=True,
                    username=publisher.reports_username,
                    password=publisher.reports_password,
                )

            publisher.reports_project_id = project_id
            publisher.reports_group_id = group_id
            publisher.reports_user_id = user_id
            publisher.save()

            AuditLog.objects.create(
                user_id=initiating_user_id,
                event_time=datetime.datetime.now(),
                action='setup-reports',
                entity_type='publisher',
                entity_id=publisher_id,
            )

        t.update_datasources_and_workbooks(publisher)
        publisher.reports_setup_status = 'completed'
        publisher.save()

    except:
        publisher.reports_setup_status = 'error'
        publisher.save()


@app.task
def update_report_item(item_type, item_id, initiating_user_id, publisher_id_list=None):
    log.info('Starting report update for %s (%s)...' % (item_type, item_id))

    try:
        status = SingletonTaskStatus.objects.get(
            task_type=item_type + '-update',
            task_id=item_id,
        )
    except SingletonTaskStatus.DoesNotExist:
        status = SingletonTaskStatus.objects.create(
            task_type=item_type + '-update',
            task_id=item_id,
        )

    # bail if an update is already under way
    if status.status == 'in-progress':
        return

    if publisher_id_list:
        publishers = PublisherMetadata.objects.filter(publisher_id__in=publisher_id_list)
    else:
        publishers = PublisherMetadata.objects.all()

    status.start_time = datetime.datetime.now()
    status.status = 'in-progress'
    status.save()

    try:
        t = TableauConnector(
            username=common.TABLEAU_USERNAME,
            password=common.TABLEAU_PASSWORD,
            server=common.TABLEAU_SERVER
        )

        for publisher in publishers:
            if item_type == 'workbook':
                if item_id in publisher.all_workbooks:
                    t.add_workbook_to_project(publisher, item_id)
            elif item_type == 'datasource':
                if item_id in publisher.all_datasources:
                    t.add_datasource_to_project(publisher, item_id)

        AuditLog.objects.create(
            user_id=initiating_user_id,
            event_time=datetime.datetime.now(),
            action='update-' + item_type,
            entity_type=item_type,
            entity_id=item_id,
        )

        status.end_time = datetime.datetime.now()
        status.status = 'completed'
        status.save()

        log.info('Finished report update')

    except:
        log.info('Error in report update')
        log.info(traceback.format_exc())
        print(traceback.format_exc())

        status.end_time = datetime.datetime.now()
        status.status = 'error'
        status.save()
