#!/usr/bin/env python
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.models import PublishedArticle, PublishedArticleByCohort, ArticleCitations

import os

os.sys.path.append(os.environ['IVETL_ROOT'])


if __name__ == "__main__":

    open_cassandra_connection()

    publisher_id = 'acs'

    ctr = 0

    for article in PublishedArticle.objects.filter(publisher_id=publisher_id).limit(10000000):

        if (article.date_of_publication.year <= 2012 and not article.is_cohort) or \
           (article.date_of_publication.year <= 2014 and article.is_cohort):

            ctr += 1

            # if article.is_cohort:
            #     print(article.date_of_publication.strftime("%Y-%m-%d"))

            doi = article.article_doi
            is_cohort = article.is_cohort

            for citation in ArticleCitations.objects.filter(publisher_id=publisher_id, article_doi=doi).limit(10000000):
                citation.delete()

            pac = PublishedArticleByCohort.objects.filter(publisher_id=publisher_id, is_cohort=is_cohort, article_doi=doi)
            if pac:
                pac.delete()

            article.delete()

    print("Deleted %s articles" % (ctr,))
    close_cassandra_connection()
