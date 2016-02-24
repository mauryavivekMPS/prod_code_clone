import datetime
from ivetl.common import common
from ivetl.models import Publisher_Metadata, Audit_Log
from ivetl.connectors import TableauConnector
from ivetl.celery import app


@app.task
def setup_reports(publisher_id, initiating_user_id):
    publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)
    publisher.reports_setup_status = 'in-progress'
    publisher.save()

    try:
        t = TableauConnector(
            username=common.TABLEAU_USERNAME,
            password=common.TABLEAU_PASSWORD,
            server=common.TABLEAU_SERVER
        )

        if publisher.demo:
            project_id, group_id, user_id = t.setup_account(
                publisher.publisher_id,
                publisher.reports_project,
            )
        else:
            project_id, group_id, user_id = t.setup_account(
                publisher.publisher_id,
                publisher.reports_project,
                create_new_login=True,
                username=publisher.reports_username,
                password=publisher.reports_password,
            )

        publisher.reports_project_id = project_id
        publisher.reports_group_id = group_id
        publisher.reports_user_id = user_id
        publisher.reports_setup_status = 'completed'
        publisher.save()

        Audit_Log.objects.create(
            user_id=initiating_user_id,
            event_time=datetime.datetime.now(),
            action='setup-reports',
            entity_type='publisher',
            entity_id=publisher_id,
        )

    except:
        publisher.reports_setup_status = 'error'
        publisher.save()
