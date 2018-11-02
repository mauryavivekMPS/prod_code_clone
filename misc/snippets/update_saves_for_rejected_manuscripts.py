#!/usr/bin/env python
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.models import RejectedArticles
from ivetl.connectors import MendeleyConnector
from ivetl.common import common

import os

os.sys.path.append(os.environ['IVETL_ROOT'])

if __name__ == "__main__":

    open_cassandra_connection()
    mendeley = MendeleyConnector(common.MENDELEY_CLIENT_ID, common.MENDELEY_CLIENT_SECRET)

    publisher_ids = [
        'aaas',
        'aha',
        'asce',
        'asm',
        'bmj',
        'cell',
        'endo',
        'jacc',
        'jama',
        'sfn',
        'wkh'
    ]

    ctr = 0

    for pid in publisher_ids:
        for manuscript in RejectedArticles.objects.filter(publisher_id=pid).limit(10000000):

            if manuscript.status in ('Published & Not Cited', 'Published & Citation Info Unavailable', 'Published & Cited'):

                ctr += 1

                print()
                print(str(ctr) + ". (" + pid + ") Getting saves for " + manuscript.crossref_doi)
                try:
                    ms = mendeley.get_saves(manuscript.crossref_doi)
                    manuscript.mendeley_saves = ms
                    manuscript.save()
                    print("Found " + str(ms) + " saves")
                except:
                    print("No saves")

        print("Updated %s manuscripts" % (ctr,))

    close_cassandra_connection()
