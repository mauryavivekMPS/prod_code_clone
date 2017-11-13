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


class UploadedFile(Model):
    publisher_id = columns.Text(partition_key=True)
    uploaded_file_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    processed_time = columns.DateTime(primary_key=True)
    product_id = columns.Text()
    pipeline_id = columns.Text()
    job_id = columns.Text()
    path = columns.Text()
    user_id = columns.UUID()
    original_name = columns.Text()
    validated = columns.Boolean()


if __name__ == "__main__":
    open_cassandra_connection()

    for f in UploadedFile.objects.all():
        f.original_name = os.path.basename(f.path)
        f.validated = True
        f.save()

    close_cassandra_connection()
