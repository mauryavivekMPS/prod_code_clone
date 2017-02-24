#!/usr/bin/env python

import django
django.setup()

import sys
import os
import datetime
import uuid
import decimal
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from cassandra.util import OrderedMapSerializedKey
from ivetl.models import *
from ivetl.common import common


models = [
    'PublishedArticle',
    'PublishedArticleValues',
    'Publisher_Vizor_Updates',
    'ArticleCitations',
    'Issn_Journal',
    'PipelineStatus',
    'PipelineTaskStatus',
    'RejectedArticles',
    'PublisherJournal',
    'Publisher_User',
    'PublisherMetadata',
    'Audit_Log',
    'PublishedArticleByCohort',
    'Scopus_Api_Key',
    'ArticleUsage',
    'Demo',
    'UptimeCheckMetadata',
    'UptimeCheckStat',
    'HighwireMetadata',
    'DrupalMetadata',
    'SystemGlobal',
    'Doi_Transform_Rule',
    'Alert',
    'Notification',
    'Notification_Summary',
    'AttributeValues',
]

def format_value(value):
    if value is None:
        return 'NULL'

    else:
        value_type = type(value)

        if value_type in [int, float, bool, uuid.UUID, decimal.Decimal]:
            return str(value)
        elif value_type is datetime.datetime:
            return "'%s'" % value.strftime('%Y-%m-%d %H:%M:%S%z')
        elif value_type is list:
            return "[%s]" % ','.join([format_value(v) for v in value])
        elif value_type in (dict, OrderedMapSerializedKey):
            return "{%s}" % ','.join(['%s:%s' % (format_value(k), format_value(v)) for k, v in value.items()])

    return "'%s'" % value.replace("'", "''").replace("\n", "\\n")


if __name__ == "__main__":

    if len(sys.argv) == 2:
        output_dir = sys.argv[1]
    else:
        output_dir = '.'

    cluster = Cluster(common.CASSANDRA_IP_LIST)
    session = cluster.connect()

    for model_name in models:
        model_class = getattr(sys.modules[__name__], model_name)
        table_name = model_class.column_family_name()
        cols = list(model_class._columns.keys())
        output_path = os.path.join(output_dir, table_name + '.csv')

        print('Exporting %s to %s' % (model_name, output_path))

        statement = SimpleStatement('select %s from %s limit 10000000;' % (','.join(cols), table_name), fetch_size=1000)

        with open(output_path, 'w') as f:
            f.write(','.join(cols) + '\n')
            for row in session.execute(statement):
                col_values = [format_value(getattr(row, col)) for col in cols]
                f.write(','.join(col_values) + '\n')
