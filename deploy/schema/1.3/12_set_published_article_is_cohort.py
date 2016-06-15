#!/usr/bin/env python

import os
os.sys.path.append(os.environ['IVETL_ROOT'])

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl.celery import open_cassandra_connection, close_cassandra_connection


class PublishedArticle(Model):
    publisher_id = columns.Text(primary_key=True)
    article_doi = columns.Text(primary_key=True)
    article_issue = columns.Text()
    article_journal = columns.Text()
    article_journal_issn = columns.Text()
    article_pages = columns.Text()
    article_publisher = columns.Text()
    article_scopus_id = columns.Text()
    article_title = columns.Text()
    article_volume = columns.Text()
    citations_updated_on = columns.DateTime()
    co_authors = columns.Text()
    created = columns.DateTime()
    date_of_publication = columns.DateTime()
    first_author = columns.Text()
    hw_metadata_retrieved = columns.Boolean()
    scopus_citation_count = columns.Integer()
    citations_updated_on = columns.DateTime()
    updated = columns.DateTime()
    article_type = columns.Text()
    subject_category = columns.Text()
    custom = columns.Text()
    custom_2 = columns.Text()
    custom_3 = columns.Text()
    editor = columns.Text()
    citations_lookup_error = columns.Boolean()
    is_open_access = columns.Text()
    from_rejected_manuscript = columns.Boolean()
    rejected_manuscript_id = columns.Text()
    rejected_manuscript_editor = columns.Text()
    date_of_rejection = columns.DateTime()
    is_cohort = columns.Boolean()
    has_abstract = columns.Boolean()

class Publisher_Metadata(Model):
    publisher_id = columns.Text(primary_key=True)
    name = columns.Text()
    hw_addl_metadata_available = columns.Boolean()
    issn_to_hw_journal_code = columns.Map(columns.Text(), columns.Text())
    published_articles_issns_to_lookup = columns.List(columns.Text())
    published_articles_last_updated = columns.DateTime()
    scopus_api_keys = columns.List(columns.Text())
    crossref_username = columns.Text()
    crossref_password = columns.Text()
    supported_products = columns.List(columns.Text())
    pilot = columns.Boolean()
    has_cohort = columns.Boolean(index=True)
    cohort_articles_issns_to_lookup = columns.List(columns.Text())
    cohort_articles_last_updated = columns.DateTime()


if __name__ == "__main__":
    open_cassandra_connection()

    publishers = Publisher_Metadata.objects.limit(1000)

    for p in publishers:

        print("\nUpdating publisher: " + p.publisher_id)
        for a in PublishedArticle.objects.filter(publisher_id=p.publisher_id).limit(5000000):

            print('.', end="")
            if a.is_cohort is True:
                pass
            else:
                a.is_cohort=False

            a.save()

    close_cassandra_connection()