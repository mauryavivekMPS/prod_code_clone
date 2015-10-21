#!/usr/bin/env python

import os
os.sys.path.append(os.environ['IVETL_ROOT'])

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl.celery import open_cassandra_connection, close_cassandra_connection


class Article_Citations(Model):
    publisher_id = columns.Text(primary_key=True)
    article_doi = columns.Text(primary_key=True)
    citation_doi = columns.Text(primary_key=True)
    citation_date = columns.DateTime()
    citation_first_author = columns.Text()
    citation_issue = columns.Text()
    citation_journal_issn = columns.Text()
    citation_journal_title = columns.Text()
    citation_pages = columns.Text()
    citation_scopus_id = columns.Text()
    citation_sources = columns.List(columns.Text())
    citation_source_scopus = columns.Boolean()
    citation_source_xref = columns.Boolean()
    citation_title = columns.Text()
    citation_volume = columns.Text()
    citation_count = columns.Integer()
    created = columns.DateTime()
    updated = columns.DateTime()

class Publisher_Metadata(Model):
    publisher_id = columns.Text(primary_key=True)
    hw_addl_metadata_available = columns.Boolean()
    issn_to_hw_journal_code = columns.Map(columns.Text(), columns.Text())
    published_articles_issns_to_lookup = columns.List(columns.Text())
    published_articles_last_updated = columns.DateTime()
    scopus_api_keys = columns.List(columns.Text())
    crossref_username = columns.Text()
    crossref_password = columns.Text()


if __name__ == "__main__":
    open_cassandra_connection()

    publishers = Publisher_Metadata.objects.limit(1000)

    for p in publishers:

        if p.publisher_id.endswith('cohort'):
            continue

        print("Updating publisher: " + p.publisher_id)
        for citation in Article_Citations.objects.filter(publisher_id=p.publisher_id).limit(5000000):

            print('.')
            if citation.citation_sources:
                if 'Scopus' in citation.citation_sources:
                    citation.citation_source_scopus = True

                if 'Crossref' in citation.citation_sources:
                    citation.citation_source_xref = True

                citation.save()
    close_cassandra_connection()
