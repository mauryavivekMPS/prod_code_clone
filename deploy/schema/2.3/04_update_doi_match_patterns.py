#!/usr/bin/env python

import os
os.sys.path.append(os.environ['IVETL_ROOT'])

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl.celery import open_cassandra_connection, close_cassandra_connection


class Doi_Transform_Rule(Model):
    journal_code = columns.Text(primary_key=True)
    type = columns.Text(primary_key=True)
    match_expression = columns.Text(primary_key=True)
    transform_spec = columns.Text()

if __name__ == "__main__":
    open_cassandra_connection()

    print('Updating match patterns for all rules to include terminators (i.e. ^ and $)...')
    for rule in Doi_Transform_Rule.objects.all():
        Doi_Transform_Rule.objects.create(
            journal_code=rule.journal_code,
            type=rule.type,
            match_expression='^' + rule.match_expression + '$',
            transform_spec=rule.transform_spec
        )
        rule.delete()

    close_cassandra_connection()
