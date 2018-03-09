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

from ivetl.models import PublishedArticle, RejectedArticles, ValueMapping, ValueMappingDisplay

publisher_id = 'ecs'


def run_clean_up():

    for a in PublishedArticle.objects.filter(publisher_id=publisher_id).limit(10000000).fetch_size(1000):
        stripped_subject_category = a.subject_category.strip()
        if stripped_subject_category != a.subject_category:
            print('published_article |%s| -> |%s|' % (a.subject_category, stripped_subject_category))
            a.subject_category = stripped_subject_category
            a.save()

    for a in RejectedArticles.objects.filter(publisher_id=publisher_id).limit(10000000).fetch_size(1000):
        stripped_subject_category = a.subject_category.strip()
        if stripped_subject_category != a.subject_category:
            print('rejected_articles: |%s| -> |%s|' % (a.subject_category, stripped_subject_category))
            a.subject_category = stripped_subject_category
            a.save()

    # if we find any original values that need stripping, delete the existing entry and add a new one
    for v in ValueMapping.objects.filter(publisher_id=publisher_id, mapping_type='subject_category'):
        stripped_original_value = v.original_value.strip()
        if stripped_original_value != v.original_value:
            print('value_mapping: |%s| -> |%s|' % (v.original_value, stripped_original_value))
            ValueMapping.objects.create(
                publisher_id=v.publisher_id,
                mapping_type=v.mapping_type,
                original_value=stripped_original_value,
                canonical_value=v.canonical_value,
            )
            v.delete()

    # if there are any display values that need stripping, do that inline
    for d in ValueMappingDisplay.objects.filter(publisher_id=publisher_id, mapping_type='subject_category'):
        stripped_display_value = d.display_value.strip()
        if stripped_display_value != d.display_value:
            print('value_mapping_display: |%s| -> |%s|' % (d.display_value, stripped_display_value))
            d.display_value = stripped_display_value
            d.save()


if __name__ == "__main__":
    run_clean_up()
