#!/usr/bin/env python
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.models import RejectedArticles

import os

os.sys.path.append(os.environ['IVETL_ROOT'])


if __name__ == "__main__":

    open_cassandra_connection()

    publisher_id = 'cshl'

    JOURNALS_TO_DELETE = [
        'Biorxiv',
        'bioRxiv'
    ]

    ctr = 0

    for manuscript in RejectedArticles.objects.filter(publisher_id=publisher_id).limit(10000000):

        if manuscript.submitted_journal in JOURNALS_TO_DELETE:

            ctr += 1

            manuscript.delete()

    print("Deleted %s manuscripts" % (ctr,))
    close_cassandra_connection()
