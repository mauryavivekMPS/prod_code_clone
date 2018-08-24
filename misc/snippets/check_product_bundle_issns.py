#!/usr/bin/env python

import os
os.sys.path.append(os.environ['IVETL_ROOT'])

from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.models import ProductBundle

if __name__ == "__main__":

    aacr_issns = [
        '1557-3125',
        '1541-7786',
        '1557-3265',
        '1078-0432',
        '1538-7755',
        '1055-9965',
        '1538-8514',
        '1535-7163',
        '1538-7445',
        '0008-5472',
        '2326-6074',
        '2326-6066',
        '1940-6215',
        '1940-6207',
        '2159-8290',
        '2159-8274'
    ]

    open_cassandra_connection()

    ctr = 0

    for pb in ProductBundle.objects.filter(publisher_id='aacr').limit(10000000):

        valid_issns = []
        invalid_issns = []

        for issn in pb.journal_issns:
            if issn in aacr_issns:
                valid_issns.append(issn)
            else:
                invalid_issns.append(issn)

        print(pb.bundle_name)
        print("Valid ISSNS:" +  ", ".join(valid_issns))
        print("Invalid ISSNS:" +  ", ".join(invalid_issns))
        print()

    close_cassandra_connection()
