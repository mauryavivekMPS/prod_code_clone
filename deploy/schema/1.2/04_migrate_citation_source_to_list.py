#!/usr/bin/env python

import os
os.sys.path.append(os.environ['IVETL_ROOT'])

from cqlengine import columns
from cqlengine.models import Model
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
    citation_source = columns.Text()  # old
    citation_sources = columns.List(columns.Text())  # new
    citation_title = columns.Text()
    citation_volume = columns.Text()
    citation_count = columns.Integer()
    created = columns.DateTime()
    updated = columns.DateTime()


if __name__ == "__main__":
    open_cassandra_connection()

    for citation in Article_Citations.objects.all():
        if citation.citation_source:
            citation.citation_sources = [citation.citation_source]
            citation.save()
    close_cassandra_connection()
