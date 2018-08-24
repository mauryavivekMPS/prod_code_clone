#!/usr/bin/env python
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.models import PublisherJournal, PublisherMetadata

import os
import requests

os.sys.path.append(os.environ['IVETL_ROOT'])


if __name__ == "__main__":

    open_cassandra_connection()

    for journal in PublisherJournal.objects.all():

        if journal.product_id == 'cohort_articles':

            publisher = PublisherMetadata.objects.get(publisher_id=journal.publisher_id)

            if not publisher.demo and not publisher.pilot:

                r = requests.get("http://api.crossref.org/journals/%s" % (journal.electronic_issn,))

                if r.ok:
                    response_json = r.json()
                    print('%s, %s, %s' % (journal.electronic_issn.strip(), response_json['message']['title'], response_json['message']['publisher']))

    close_cassandra_connection()
