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
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.common import common


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


class InstitutionUsageJournal(Model):
    publisher_id = columns.Text(partition_key=True)
    counter_type = columns.Text(primary_key=True)
    journal = columns.Text(primary_key=True)


class PublisherMetadata(Model):
    publisher_id = columns.Text(primary_key=True)
    name = columns.Text()
    email = columns.Text()
    hw_addl_metadata_available = columns.Boolean()
    issn_to_hw_journal_code = columns.Map(columns.Text(), columns.Text())
    published_articles_issns_to_lookup = columns.List(columns.Text())
    published_articles_last_updated = columns.DateTime()
    scopus_api_keys = columns.List(columns.Text())
    crossref_username = columns.Text()
    crossref_password = columns.Text()
    reports_username = columns.Text()
    reports_password = columns.Text()
    reports_project = columns.Text()
    reports_user_id = columns.Text()
    reports_group_id = columns.Text()
    reports_project_id = columns.Text()
    reports_setup_status = columns.Text()
    scopus_key_setup_status = columns.Text()
    supported_product_groups = columns.List(columns.Text())  # type: list
    supported_products = columns.List(columns.Text())  # type: list
    pilot = columns.Boolean()
    demo = columns.Boolean(index=True)
    demo_id = columns.Text(index=True)
    has_cohort = columns.Boolean(index=True)
    cohort_articles_issns_to_lookup = columns.List(columns.Text())
    cohort_articles_last_updated = columns.DateTime()
    ac_databases = columns.List(columns.Text())
    archived = columns.Boolean(default=False, index=True)


if __name__ == "__main__":
    open_cassandra_connection()

    cluster = Cluster(common.CASSANDRA_IP_LIST)
    session = cluster.connect()

    all_usage_sql = """
        select *
        from impactvizor.institution_usage_stat
        where publisher_id = %s
        and counter_type = %s
        limit 10000000
    """

    all_usage_statement = SimpleStatement(all_usage_sql, fetch_size=1000)

    for publisher in PublisherMetadata.objects.all():
        publisher_id = publisher.publisher_id

        if publisher_id == 'asm':
            print('skipping asm')
            continue

        print(publisher_id)

        publisher_journals = set()

        count = 0
        for counter_type in ('jr2', 'jr3'):
            print(counter_type)

            for u in session.execute(all_usage_statement, (publisher_id, counter_type)):
                count += 1

                if u.journal not in publisher_journals:
                    InstitutionUsageJournal.objects.create(
                        publisher_id=publisher_id,
                        counter_type=counter_type,
                        journal=u.journal,
                    )
                    publisher_journals.add(u.journal)

                InstitutionUsageStatComposite.objects.create(
                    publisher_id=u.publisher_id,
                    counter_type=u.counter_type,
                    journal=u.journal,
                    subscriber_id=u.subscriber_id,
                    usage_date=u.usage_date,
                    usage_category=u.usage_category,
                    journal_print_issn=u.journal_print_issn,
                    journal_online_issn=u.journal_online_issn,
                    institution_name=u.institution_name,
                    usage=u.usage,
                    bundle_name=u.bundle_name,
                    amount=u.amount,
                    trial=u.trial,
                    trial_expiration_date=u.trial_expiration_date,
                )

                if not count % 1000:
                    print(count)

        print(count)

    close_cassandra_connection()
