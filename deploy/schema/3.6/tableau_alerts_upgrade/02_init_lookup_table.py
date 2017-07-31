#!/usr/bin/env python

import os

os.sys.path.append(os.environ['IVETL_ROOT'])

import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl.celery import open_cassandra_connection, close_cassandra_connection


class TableauNotification(Model):
    notification_id = columns.UUID(partition_key=True, default=uuid.uuid4, index=True)
    alert_id = columns.UUID(index=True)
    publisher_id = columns.Text()
    template_id = columns.Text()
    notification_date = columns.DateTime()
    expiration_date = columns.DateTime()
    name = columns.Text()
    alert_params = columns.Text()
    alert_filters = columns.Text()
    custom_message = columns.Text()


class TableauNotificationByAlert(Model):
    publisher_id = columns.Text(partition_key=True)
    alert_id = columns.UUID(primary_key=True)
    notification_id = columns.UUID(primary_key=True)
    notification_date = columns.DateTime()


if __name__ == "__main__":
    open_cassandra_connection()

    for n in TableauNotification.objects.all().fetch_size(1000).limit(1000000):
        TableauNotificationByAlert.objects.create(
            publisher_id=n.publisher_id,
            alert_id=n.alert_id,
            notification_id=n.notification_id,
            notification_date=n.notification_date,
        )

    close_cassandra_connection()
