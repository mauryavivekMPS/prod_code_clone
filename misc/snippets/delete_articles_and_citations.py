#!/usr/bin/env python
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.models import PublishedArticle, PublishedArticleByCohort, ArticleCitations

import os

os.sys.path.append(os.environ['IVETL_ROOT'])


if __name__ == "__main__":

    open_cassandra_connection()

    publisher_id = 'wkh'

    JOURNALS_TO_DELETE = [
        'JONA The Journal of Nursing Administration',
        'AJN American Journal of Nursing',
        'The Nurse Practitioner',
        'Nurse Leader',
        'Nursing Management (Springhouse)',
        'Nursing',
        'The Journal for Nurse Practitioners',
        'Journal of the American Association of Nurse Practitioners']

    ctr = 0

    for article in PublishedArticle.objects.filter(publisher_id=publisher_id).limit(10000000):

        if article.article_journal in JOURNALS_TO_DELETE:

            ctr += 1
            doi = article.article_doi
            is_cohort = article.is_cohort

            for citation in ArticleCitations.objects.filter(publisher_id=publisher_id, article_doi=doi).limit(10000000):
                citation.delete()

            pac = PublishedArticleByCohort.objects.filter(publisher_id=publisher_id, is_cohort=is_cohort, article_doi=doi)
            if pac:
                pac.delete()

            article.delete()

            # Not deleting published article values as wkh did not upload a foam file for these journals

    print("Deleted %s articles" % (ctr,))
    close_cassandra_connection()
