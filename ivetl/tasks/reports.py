import datetime
import traceback
import requests
from ivetl.common import common
from ivetl.models import PublisherMetadata, SingletonTaskStatus
from ivetl.connectors import TableauConnector
from ivetl.celery import app
from ivetl import utils


@app.task
def update_reports_for_publisher(publisher_id, initiating_user_id, include_initial_setup=False):
    print('Starting report update for %s...' % publisher_id)

    PublisherMetadata.objects(publisher_id=publisher_id).update(
        reports_setup_status='in-progress',
    )

    publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)
    reports_username = publisher.reports_username
    reports_password = publisher.reports_password

    try:
        t = TableauConnector(
            username=common.TABLEAU_USERNAME,
            password=common.TABLEAU_PASSWORD,
            server=common.TABLEAU_SERVER
        )

        if include_initial_setup:
            print('Running initial setup')
            if publisher.demo:
                project_id, group_id, user_id = t.setup_account(publisher)
            else:
                project_id, group_id, user_id = t.setup_account(
                    publisher,
                    create_new_login=True,
                    username=reports_username,
                    password=reports_password,
                )

            PublisherMetadata.objects(publisher_id=publisher_id).update(
                reports_project_id=project_id,
                reports_group_id = group_id,
                reports_user_id = user_id,
            )

            utils.add_audit_log(
                user_id=initiating_user_id,
                publisher_id=publisher_id,
                action='setup-reports',
                description='Setup reports for %s' % publisher_id,
            )
        else:
            print('Skipping initial setup')

        print('Updating datasources and workbooks')
        publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)
        t.update_datasources_and_workbooks(publisher)

        PublisherMetadata.objects(publisher_id=publisher_id).update(
            reports_setup_status='completed',
        )

        print('Completed update')

    except:
        print('Error in report update:')
        print(traceback.format_exc())

        PublisherMetadata.objects(publisher_id=publisher_id).update(
            reports_setup_status='error',
        )


@app.task
def update_report_item(item_type, item_id, initiating_user_id, publisher_id_list=None, skip_demo_publishers=True):
    print('Starting report update for %s (%s)...' % (item_type, item_id))

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
            print('Looking at publisher: %s' % publisher.publisher_id)

            if skip_demo_publishers and (publisher.demo or publisher.pilot):
                print('Not a production publisher, skipping')
                continue

            try:
                if item_type == 'workbook':
                    if item_id in publisher.all_workbooks:
                        t.add_workbook_to_project(publisher, item_id)
                        print('Updating workbook')
                    else:
                        print('Workbook not supported by pub, skipping')
                elif item_type == 'datasource':
                    if item_id in publisher.all_datasources:
                        ds = t.add_datasource_to_project(publisher, item_id)
                        tid = ds['tableau_id']
                        t.create_extract(tid)
                        print('Updating datasource')
                    else:
                        print('Datasource not supported by pub, skipping')

            except requests.HTTPError as e:
                print('Error running update:')
                print(traceback.format_exc())
                print('Response content:')
                print(e.response.content)
                continue

            utils.add_audit_log(
                user_id=initiating_user_id,
                publisher_id=publisher.publisher_id,
                action='update-' + item_type,
                description='Update datasource %s' % item_id,
            )

        status.end_time = datetime.datetime.now()
        status.status = 'completed'
        status.save()

        print('Finished report update')

    except:
        print('Error in report update:')
        print(traceback.format_exc())

        status.end_time = datetime.datetime.now()
        status.status = 'error'
        status.save()
