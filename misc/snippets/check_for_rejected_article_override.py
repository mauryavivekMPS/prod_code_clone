#!/usr/bin/env python

import os
os.sys.path.append(os.environ['IVETL_ROOT'])
from cassandra.cqlengine.query import DoesNotExist
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.models import RejectedArticleOverride

try:
    open_cassandra_connection()
except:
    pass

def has_rejected_article_override(publisher_id, manuscript_id, doi):
    try:
        override = RejectedArticleOverride.objects.get(
            publisher_id=publisher_id,
            manuscript_id=manuscript_id,
            doi=doi
        )
        print('Finished lookup')
        if override:
            print('Override exists')
            print('True')
            return True
    except DoesNotExist:
        print('DoesNotExist')
        print('False')
    except Exception as inst:
        print('Unexpected exception')
        print('False')
        print(inst)
    return False

if has_rejected_article_override(publisher_id='demo', manuscript_id='MS-01',
    doi='10.9000/test.doi'):
    print('has_rejected_article_override')
else:
    print('does not have rejected_article_override')

close_cassandra_connection()
