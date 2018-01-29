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

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl.celery import open_cassandra_connection, close_cassandra_connection


class InstitutionUsageStat(Model):
    publisher_id = columns.Text(partition_key=True)
    counter_type = columns.Text(partition_key=True)
    journal = columns.Text(partition_key=True)
    subscriber_id = columns.Text(primary_key=True)
    usage_date = columns.DateTime(primary_key=True, index=True)
    usage_category = columns.Text(primary_key=True)
    journal_print_issn = columns.Text()
    journal_online_issn = columns.Text()
    institution_name = columns.Text()
    usage = columns.Integer()
    bundle_name = columns.Text()
    amount = columns.Decimal()
    trial = columns.Boolean()
    trial_expiration_date = columns.DateTime()


class InstitutionUsageStatComposite(Model):
    publisher_id = columns.Text(partition_key=True)
    counter_type = columns.Text(primary_key=True)
    journal = columns.Text(primary_key=True)
    subscriber_id = columns.Text(primary_key=True)
    usage_date = columns.DateTime(primary_key=True)
    usage_category = columns.Text(primary_key=True)
    journal_print_issn = columns.Text()
    journal_online_issn = columns.Text()
    institution_name = columns.Text()
    usage = columns.Integer()
    bundle_name = columns.Text()
    amount = columns.Decimal()
    trial = columns.Boolean()
    trial_expiration_date = columns.DateTime()


class InstitutionUsageJournal(Model):
    publisher_id = columns.Text(partition_key=True)
    counter_type = columns.Text(primary_key=True)
    journal = columns.Text(primary_key=True)


if __name__ == "__main__":
    open_cassandra_connection()

count = 0
for stat in InstitutionUsageStat.objects.filter(publisher_id='aaas').fetch_size(1000):
    count += 1
print(count)
    print(stat.journal, stat.usage)
        stat = InstitutionUsageStat.objects.create(
            publisher_id=stat.publisher_id,
            counter_type=stat.counter_type,
            journal=stat.journal,
            subscriber_id=stat.subscriber_id,
            usage_date=stat.usage_date,
            usage_category=stat.usage_category,
            journal_print_issn=stat.journal_print_issn,
            journal_online_issn=stat.journal_online_issn,
            institution_name=stat.institution_name,
            usage=stat.usage,
            bundle_name=stat.bundle_name,
            amount=stat.amount,
            trial=stat.trial,
            trial_expiration_date=stat.trial_expiration_date,
        )

    close_cassandra_connection()
