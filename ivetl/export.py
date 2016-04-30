#!/usr/bin/env python

import django
django.setup()

import sys
import datetime
from ivetl.models import *

models = [
    'Published_Article',
    'Published_Article_Values',
    'Publisher_Vizor_Updates',
    'Article_Citations',
    'Issn_Journal',
    'Pipeline_Status',
    'Pipeline_Task_Status',
    'Rejected_Articles',
    'Publisher_Journal',
    'Publisher_User',
    'Publisher_Metadata',
    'Audit_Log',
    'Published_Article_By_Cohort',
    'Scopus_Api_Key',
    'Article_Usage',
    'Demo',
    'Uptime_Check_Metadata',
    'Uptime_Check_Stat',
    'Highwire_Metadata',
    'Drupal_Metadata',
    'System_Global',
    'Doi_Transform_Rule',
    'Alert',
    'Notification',
    'Notification_Summary',
    'Attribute_Values',
]

def format_value(value):
    if value is None:
        return 'NULL'

    else:
        value_type = type(value)

        if value_type in [int, float, bool]:
            return str(value)
        elif value_type is datetime.datetime:
            return "'%s'" % value.strftime('%Y-%m-%d %H:%M:%S%z')
        elif value_type is list:
            return "[%s]" % ','.join([format_value(v) for v in value])
        elif value_type is dict:
            return "{%s}" % ','.join(['%s:%s' % (format_value(k), format_value(v)) for k, v in value.items()])

    return "'%s'" % value

if __name__ == "__main__":

    for model_name in models:
        print('Exporting %s' % model_name)

        model_class = getattr(sys.modules[__name__], model_name)
        table_name = model_class.column_family_name()
        cols = list(model_class._columns.keys())

        with open(table_name + '.csv', 'w') as f:
            f.write(','.join(cols) + '\n')
            for instance in model_class.objects.all():
                col_values = [format_value(instance[col]) for col in cols]
                f.write(','.join(col_values) + '\n')
