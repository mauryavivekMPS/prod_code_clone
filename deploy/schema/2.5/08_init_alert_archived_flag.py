#!/usr/bin/env python

import os
os.sys.path.append(os.environ['IVETL_ROOT'])

import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl.celery import open_cassandra_connection, close_cassandra_connection


class Alert(Model):
    alert_id = columns.UUID(primary_key=True, default=uuid.uuid4, index=True)
    publisher_id = columns.Text(partition_key=True)
    name = columns.Text()
    check_id = columns.Text(primary_key=True)
    check_params = columns.Text()
    filter_params = columns.Text()
    emails = columns.List(columns.Text())
    enabled = columns.Boolean()
    archived = columns.Boolean()


if __name__ == "__main__":
    open_cassandra_connection()

    print('Setting all alert flags to false...')
    for a in Alert.objects.all():
        a.archived = False
        a.save()

    close_cassandra_connection()
