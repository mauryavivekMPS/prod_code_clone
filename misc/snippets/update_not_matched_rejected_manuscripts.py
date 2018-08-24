#!/usr/bin/env python
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.models import RejectedArticles

import os

os.sys.path.append(os.environ['IVETL_ROOT'])


if __name__ == "__main__":

    open_cassandra_connection()

    publisher_id = 'acs'

    ctr = 0

    for m in RejectedArticles.objects.filter(publisher_id=publisher_id).limit(10000000):

        if m.status == 'Not Published' and m.published_journal is not None:

            m.crossref_doi = None
            m.crossref_match_score = None
            m.date_of_publication = None

            m.published_co_authors = None
            m.published_first_author = None
            m.published_journal = None
            m.published_journal_issn = None
            m.published_publisher = None
            m.published_title = None
            m.scopus_doi_status = None
            m.scopus_id = None

            ctr += 1

            m.save()

    print("Updated %s manuscripts" % (ctr,))
    close_cassandra_connection()
