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

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl.celery import open_cassandra_connection, close_cassandra_connection


class SystemGlobal(Model):
    name = columns.Text(primary_key=True)
    int_value = columns.Integer()
    text_value = columns.Text()
    date_value = columns.DateTime()


if __name__ == "__main__":
    open_cassandra_connection()

    try:
        site_uptime = SystemGlobal.objects.get(name='site_uptime_high_water')
        SystemGlobal.objects.create(
            name='highwire_sites_site_uptime_hw_high_water',
            date_value=site_uptime.date_value,
        )
        site_uptime.delete()
    except SystemGlobal.DoesNotExist:
        pass

    try:
        service_stats = SystemGlobal.objects.get(name='service_stats_high_water')
        SystemGlobal.objects.create(
            name='highwire_sites_service_stats_hw_high_water',
            date_value=service_stats.date_value,
        )
        service_stats.delete()
    except SystemGlobal.DoesNotExist:
        pass

    close_cassandra_connection()
