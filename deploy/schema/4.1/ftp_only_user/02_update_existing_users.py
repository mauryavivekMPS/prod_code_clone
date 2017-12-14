# !/usr/bin/env python

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
    user_type = columns.Integer()

    # 10 publisher ftp only
    # 20 publisher staff
    # 30 highwire stff
    # 40 superuser


if __name__ == "__main__":
    open_cassandra_connection()

    for user in User.objects.all():
        if user.superuser:
            user.user_type = 40
        elif user.staff:
            user.user_type = 30
        else:
            user.user_type = 20

        user.save()

    close_cassandra_connection()
