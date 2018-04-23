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
from cassandra.cluster import Cluster
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.common import common


class User(Model):
    user_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    email = columns.Text(index=True)
    password = columns.Text()
    first_name = columns.Text()
    last_name = columns.Text()
    user_type = columns.Integer()


if __name__ == "__main__":
    open_cassandra_connection()

    cluster = Cluster(common.CASSANDRA_IP_LIST)
    session = cluster.connect()

    for user in User.objects.all():
        lowercase_email = user.email.lower()
        if lowercase_email != user.email:
            user.email = lowercase_email
            user.save()

    close_cassandra_connection()
