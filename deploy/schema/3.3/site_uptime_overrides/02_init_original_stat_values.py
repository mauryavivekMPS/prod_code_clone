#!/usr/bin/env python

import os
os.sys.path.append(os.environ['IVETL_ROOT'])

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl.celery import open_cassandra_connection, close_cassandra_connection


class UptimeCheckStat(Model):
    publisher_id = columns.Text(primary_key=True)
    check_id = columns.Integer(primary_key=True)
    check_date = columns.DateTime(primary_key=True)
    avg_response_ms = columns.Integer(default=0)
    total_up_sec = columns.Integer(default=0)
    total_down_sec = columns.Integer(default=0)
    total_unknown_sec = columns.Integer(default=0)
    original_avg_response_ms = columns.Integer(default=0)
    original_total_up_sec = columns.Integer(default=0)
    original_total_down_sec = columns.Integer(default=0)
    original_total_unknown_sec = columns.Integer(default=0)
    override = columns.Boolean()


if __name__ == "__main__":
    open_cassandra_connection()

    for s in UptimeCheckStat.objects.all().limit(100000000):
        save_this_one = False

        if s.original_avg_response_ms is None:
            s.original_avg_response_ms = s.avg_response_ms
            s.original_total_up_sec = s.total_up_sec
            s.original_total_down_sec = s.total_down_sec
            s.original_total_unknown_sec = s.total_unknown_sec
            save_this_one = True

        if s.override is None:
            s.override = False
            save_this_one = True

        if save_this_one:
            s.save()

    close_cassandra_connection()
