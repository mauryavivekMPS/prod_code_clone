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

import threading
from ivetl.connectors import CrossrefConnector
from ivetl.models import PublisherMetadata, PublishedArticle

publisher_id = 'cell'

publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)
crossref = CrossrefConnector(publisher.crossref_username, publisher.crossref_password)

all_dois = [a.article_doi for a in PublishedArticle.objects.filter(publisher_id=publisher_id).fetch_size(1000).limit(10000)]


def get_all_articles(doi_list):
    count = 0
    for doi in doi_list:
        count += 1
        print(count)
        # try:
        print('get article %s' % doi)
        crossref.get_article(doi)
        print('no exception')
        # except:
        #     print('exception')

# threading.Thread(target=get_all_articles, args=(all_dois[:20],)).start()
# threading.Thread(target=get_all_articles, args=(all_dois[20:40],)).start()
# threading.Thread(target=get_all_articles, args=(all_dois[40:60],)).start()
# threading.Thread(target=get_all_articles, args=(all_dois[60:80],)).start()

if len(sys.argv) > 1:
    start = int(sys.argv[1])
else:
    start = 0

end = start + 2000

get_all_articles(all_dois[start:end])
