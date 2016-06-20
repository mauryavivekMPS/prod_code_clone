#!/usr/bin/env python

import os
os.sys.path.append(os.environ['IVETL_ROOT'])

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl.celery import open_cassandra_connection, close_cassandra_connection


class Rejected_Articles(Model):
    publisher_id = columns.Text(primary_key=True)
    rejected_article_id = columns.TimeUUID(primary_key=True)
    article_type = columns.Text(required=False)
    authors_match_score = columns.Decimal(required=False)
    citation_lookup_status = columns.Text(required=False)
    citations = columns.Integer(required=False)
    co_authors = columns.Text(required=False)
    corresponding_author = columns.Text(required=False)
    created = columns.DateTime()
    crossref_doi = columns.Text(required=False)
    crossref_match_score = columns.Decimal(required=False)
    custom = columns.Text(required=False)
    date_of_publication = columns.DateTime(required=False)
    date_of_rejection = columns.DateTime()
    editor = columns.Text()
    first_author = columns.Text(required=False)
    keywords = columns.Text(required=False)
    manuscript_id = columns.Text(index=True)
    manuscript_title = columns.Text()
    published_co_authors = columns.Text(required=False)
    published_first_author = columns.Text(required=False)
    published_journal = columns.Text(required=False)
    published_journal_issn = columns.Text(required=False)
    published_publisher = columns.Text(required=False)
    published_title = columns.Text(required=False)
    reject_reason = columns.Text()
    scopus_doi_status = columns.Text(required=False)
    scopus_id = columns.Text(required=False)
    source_file_name = columns.Text()
    status = columns.Text()
    subject_category = columns.Text(required=False)
    submitted_journal = columns.Text(index=True)
    mendeley_saves = columns.Integer(required=False)
    preprint_doi = columns.Text(required=False)
    updated = columns.DateTime()

if __name__ == "__main__":
    open_cassandra_connection()

    print('Updating ASBMB ...')
    for ra in Rejected_Articles.objects.filter(publisher_id="asbmb").limit(1000000):
        if ra.submitted_journal == 'JBC':
            ra.submitted_journal = 'Journal of Biological Chemistry'
            ra.save()

    close_cassandra_connection()
