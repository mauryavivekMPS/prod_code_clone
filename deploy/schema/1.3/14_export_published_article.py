#!/usr/bin/env python

import os
from datetime import datetime
os.sys.path.append(os.environ['IVETL_ROOT'])

from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.models import Published_Article, Published_Article_By_Cohort, Publisher_Metadata


if __name__ == "__main__":
    open_cassandra_connection()

    updated = datetime.today()

    publishers = Publisher_Metadata.objects.limit(1000)

    for p in publishers:

        print("\nAdding publisher: " + p.publisher_id)

        for a in Published_Article.objects.filter(publisher_id=p.publisher_id).limit(5000000):

            print('.', end='')
            Published_Article_By_Cohort.create(
                publisher_id=a.publisher_id,
                is_cohort=a.is_cohort,
                article_doi=a.article_doi,
                article_scopus_id=a.article_scopus_id,
                updated=updated
            )

    close_cassandra_connection()