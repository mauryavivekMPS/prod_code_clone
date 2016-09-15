#!/usr/bin/env python

import os
os.sys.path.append(os.environ['IVETL_ROOT'])

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.common import common


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

    for p in PublisherMetadata.objects.all():

        if 'published_articles' in p.supported_products:
            if 'article_citations' not in p.supported_products:
                print('Adding article_citations to ' + p.publisher_id)
                p.supported_products.append('article_citations')

        if 'cohort_articles' in p.supported_products:
            if 'cohort_citations' not in p.supported_products:
                print('Adding cohort_citations to ' + p.publisher_id)
                p.supported_products.append('cohort_citations')

        if 'published_articles' in p.supported_products or 'rejected_manuscripts' in p.supported_products or 'cohort_articles' in p.supported_products:
            if 'impact_vizor' not in p.supported_product_groups:
                print('Adding impact_vizor to ' + p.publisher_id)
                p.supported_product_groups.append('impact_vizor')

        if 'institutions' in p.supported_products:
            if 'usage_vizor' not in p.supported_product_groups:
                print('Adding usage_vizor to ' + p.publisher_id)
                p.supported_product_groups.append('usage_vizor')

        supported_products_set = set()
        for product_group_id in p.supported_product_groups:
            for product_id in common.PRODUCT_GROUP_BY_ID[product_group_id]['products']:
                supported_products_set.add(product_id)
        p.supported_products = list(supported_products_set)

        p.save()

    close_cassandra_connection()
