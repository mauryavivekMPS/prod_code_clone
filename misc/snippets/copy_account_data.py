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

from ivetl.models import PublishedArticle, RejectedArticles

original_publisher_id = 'blood'
new_publisher_id = 'foo'


def run_copy():

    #
    # first, copy all non-cohort articles
    #

    for article in PublishedArticle.objects.filter(publisher_id=original_publisher_id, is_cohort=False):
        article.publisher_id = new_publisher_id
        article.save()

    #
    # second, rejected articles
    #

    for article in RejectedArticles.objects.filter(publisher_id=original_publisher_id):
        article.publisher_id = new_publisher_id
        article.save()



if __name__ == "__main__":
    run_copy()
