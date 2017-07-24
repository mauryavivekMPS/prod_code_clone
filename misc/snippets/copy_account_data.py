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

from ivetl.models import PublishedArticle

def run_copy():
    pass

if __name__ == "__main__":
    run_copy()
