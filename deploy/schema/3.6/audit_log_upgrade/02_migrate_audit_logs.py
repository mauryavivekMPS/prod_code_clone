#!/usr/bin/env python

import os
import sys

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'ivweb.settings.local'

if os.environ['IVETL_ROOT'] not in os.sys.path:
    sys.path.insert(0, os.environ['IVETL_ROOT'])

# new setup for 1.7 and above
import django

django.setup()

import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl.celery import open_cassandra_connection, close_cassandra_connection


class User(Model):
    user_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    email = columns.Text(index=True)
    password = columns.Text()
    first_name = columns.Text()
    last_name = columns.Text()
    staff = columns.Boolean()
    superuser = columns.Boolean()


class AuditLog(Model):
    user_id = columns.UUID(primary_key=True)
    event_time = columns.DateTime(primary_key=True)
    action = columns.Text(primary_key=True)
    entity_type = columns.Text()
    entity_id = columns.Text()


class AuditLogByUser(Model):
    user_id = columns.UUID(partition_key=True)
    event_time = columns.DateTime(primary_key=True)
    action = columns.Text(primary_key=True)
    publisher_id = columns.Text()
    description = columns.Text()


class AuditLogByPublisher(Model):
    publisher_id = columns.Text(partition_key=True)
    event_time = columns.DateTime(primary_key=True)
    action = columns.Text(primary_key=True)
    user_id = columns.UUID()
    description = columns.Text()


class AuditLogByTime(Model):
    month = columns.Text(partition_key=True)
    event_time = columns.DateTime(primary_key=True)
    action = columns.Text(primary_key=True)
    publisher_id = columns.Text()
    user_id = columns.UUID()
    description = columns.Text()


if __name__ == "__main__":
    open_cassandra_connection()

    for log in AuditLog.objects.all().fetch_size(1000).limit(1000000):

        user_id_to_email = {str(u.user_id): u.email for u in User.objects.all()}
        if log.entity_type == 'user':
            entity_description = user_id_to_email[str(log.user_id)]
        else:
            entity_description = log.entity_id

        description = log.action.replace('-', ' ').capitalize() + ' ' + entity_description

        AuditLogByUser.objects.create(
            user_id=log.user_id,
            event_time=log.event_time,
            action=log.action,
            publisher_id='unknown',
            description=description,
        )

        AuditLogByPublisher.objects.create(
            publisher_id='unknown',
            event_time=log.event_time,
            action=log.action,
            user_id=log.user_id,
            description=description,
        )

        AuditLogByTime.objects.create(
            month=log.event_time.strftime('%Y%m'),
            event_time=log.event_time,
            action=log.action,
            publisher_id='unknown',
            user_id=log.user_id,
            description=description,
        )

    close_cassandra_connection()
