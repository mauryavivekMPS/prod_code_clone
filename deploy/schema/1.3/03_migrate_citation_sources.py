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


if __name__ == "__main__":
    open_cassandra_connection()

    ctr = 0
    for citation in Article_Citations.objects.limit(5000000):

        ctr += 1
        print("Updating #" + ctr)
        
        if citation.citation_sources:
            if 'Scopus' in citation.citation_sources:
                citation.citation_source_scopus = True

            if 'Crossref' in citation.citation_sources:
                citation.citation_source_xref = True

            citation.save()
    close_cassandra_connection()
