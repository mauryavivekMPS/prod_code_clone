#!/usr/bin/env python

import os
os.sys.path.append(os.environ['IVETL_ROOT'])

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl.celery import open_cassandra_connection, close_cassandra_connection


class Publisher_Metadata(Model):
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
    supported_products = columns.List(columns.Text())
    pilot = columns.Boolean()
    demo = columns.Boolean(index=True)
    demo_id = columns.Text(index=True)
    has_cohort = columns.Boolean(index=True)
    cohort_articles_issns_to_lookup = columns.List(columns.Text())
    cohort_articles_last_updated = columns.DateTime()
    archived = columns.Boolean(default=False, index=True)

if __name__ == "__main__":
    open_cassandra_connection()

    print('Setting all publisher demo flags to false...')
    for p in Publisher_Metadata.objects.all():
        if not p.demo:
            p.demo = False
            p.save()

    close_cassandra_connection()
