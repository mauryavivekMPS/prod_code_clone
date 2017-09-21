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

import json
from ivetl.models import TableauAlert


def update():
    for a in TableauAlert.objects.filter(publisher_id='aha'):
        print('alert_id = %s' % a.alert_id)

        params = json.loads(a.alert_params)
        keys = params.keys()
        for k in keys:

            if k == 'Mendeley Metrics':
                print('updating mendeley metric')
                params['Mendeley Metric'] = params[k]
                del params[k]

            elif k == 'Cites Metrics':
                print('updating cites metric')
                params['Cite Metric'] = params[k]
                del params[k]

            elif k == 'Usage Metrics':
                print('updating usage metric')
                params['Usage Metric'] = params[k]
                del params[k]

        a.alert_params = json.dumps(params)
        a.save()

if __name__ == "__main__":
    update()
