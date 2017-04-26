#!/usr/bin/env python

import os

os.sys.path.append(os.environ['IVETL_ROOT'])

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.common import common
from ivetl.connectors import TableauConnector


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


class WorkbookUrl(Model):
    publisher_id = columns.Text(partition_key=True)
    workbook_id = columns.Text(primary_key=True)
    url = columns.Text()


if __name__ == "__main__":
    open_cassandra_connection()

    publishers_by_project_id = {}
    for publisher in PublisherMetadata.objects.all():
        publishers_by_project_id[publisher.reports_project_id] = publisher

    t = TableauConnector(
        username=common.TABLEAU_USERNAME,
        password=common.TABLEAU_PASSWORD,
        server=common.TABLEAU_SERVER
    )

    workbooks = t.list_workbooks()

    print('Found %s workbooks in Tableau' % len(workbooks))

    for workbook in workbooks:
        publisher = publishers_by_project_id.get(workbook['project_id'])
        if publisher:
            local_workbook_metadata = common.TABLEAU_WORKBOOKS_BY_NAME.get(workbook['name'])
            if local_workbook_metadata:
                workbook_id = local_workbook_metadata['id']

                print('Found an owner, adding URL for (%s, %s, %s)' % (publisher.publisher_id, workbook_id, workbook['url']))
                WorkbookUrl.objects(
                    publisher_id=publisher.publisher_id,
                    workbook_id=workbook_id,
                ).update(
                    url=workbook['url']
                )

    close_cassandra_connection()
