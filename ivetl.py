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

import argparse
from ivetl.tools import clean_tableau_filter_fields

commands = [
    'clean_filters_for_publisher',
    'clean_filters_for_all_publishers',
]


def exit_with_error(message):
    print(message)
    exit(1)


if __name__ == "__main__":
    first_parser = argparse.ArgumentParser()
    second_parser = argparse.ArgumentParser()
    first_parser.add_argument('command', choices=commands)
    second_parser.add_argument('command', choices=commands)

    args, extra_args = first_parser.parse_known_args()

    if args.command == 'clean_filters_for_publisher':
        second_parser.add_argument('publisher_id')
        clean_filters_args = second_parser.parse_args()
        clean_tableau_filter_fields.clean_filters_for_publisher(clean_filters_args.publisher_id)

    elif args.command == 'clean_filters_for_all_publishers':
        clean_tableau_filter_fields.clean_filters_for_all_publishers()
