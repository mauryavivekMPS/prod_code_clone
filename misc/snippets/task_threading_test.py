#!/usr/bin/env python

import os
import sys

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'ivweb.settings.local'

if os.environ['IVETL_ROOT'] not in os.sys.path:
    sys.path.insert(0, os.environ['IVETL_ROOT'])

# new setup for 1.7 and above
import django

django.setup()

import time
import threading
from ivetl.connectors import CrossrefConnector
from ivetl.models import PublisherMetadata, PublishedArticle

publisher_id = 'cell'


def get_all_articles(doi_list):
    print('started thread get_all_articles')
    publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)
    crossref = CrossrefConnector(publisher.crossref_username, publisher.crossref_password)

    count = 0
    for doi in doi_list:
        count += 1
        print('%s %s. get article %s' % (threading.get_ident(), count, doi))
        if '2014.09.002' in doi:
            time.sleep(3)
        crossref.get_article(doi)


def run_test():
    print('starting test')
    all_dois = [a.article_doi for a in PublishedArticle.objects.filter(publisher_id=publisher_id).fetch_size(1000).limit(100)]

    t1 = threading.Thread(target=get_all_articles, args=(all_dois[:10],))
    t1.start()
    t2 = threading.Thread(target=get_all_articles, args=(all_dois[20:30],))
    t2.start()

    t1.join()
    t2.join()

    print('both threads finished!')


if __name__ == "__main__":
    run_test()
