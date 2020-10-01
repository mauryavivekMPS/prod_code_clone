# !/usr/bin/env python
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.models import PublishedArticle

import sys
import os
import time
import csv
import re
from getopt import getopt
import traceback

os.sys.path.append(os.environ['IVETL_ROOT'])

opts, args = getopt(sys.argv[1:], 'h:p:j:o:e:t:', [
    'help',
    'publisher',
    'journal',
    'outfile',
    'exportfile,'
    'toc'])

pubid = None
journal = None
exportfile = 'published_article_type_clean_export.tsv'
test = False

helptext = '''usage: python export_published_article_values.py -- [ -h ] -p publisher_id -j article_journal
Query the published_article_values table in Cassandra and export values for analysis.
Environment variables:
This script uses the open_cassandra_connection and close_cassandra_connection
routines defined in celery.py, which in turn use variables defined in common.py.
The Cassandra IP list can be set with the following variable, e.g:
export IVETL_CASSANDRA_IP=bk-vizor-dev-01.highwire.org
Use a comma separated list for multiple hosts.
Options and arguments:
-h     :  print this help message and exit (also --help)
-o     :  output file path to write to. Default: /iv/working/misc/{publisher-id}-rejected_article_export.tsv
-p     :  publisher_id value to use when querying cassandra. required.
-j     :  article_journal value to use when querying cassandra.
-t     :  exports data to output file without actually updating cassandra.
'''

basedir = '/iv/working/misc/'

for opt in opts:
    if opt[0] == '-h':
        print(helptext)
        sys.exit()
    if opt[0] == '-t':
        toc = True
        print('initializing TOC overwrite')
    if opt[0] == '-p':
        pubid = opt[1]
        print('initializing single publisher run: %s' % pubid)
    if opt[0] == '-j':
        journal = opt[1]
        print('initializing single journal run: %s' % journal)
    if opt[0] == '-o':
        exportfile = opt[1]
        basedir = ''
        print('initializing output file: %s' % exportfile)

if basedir == '/iv/working/misc/':
    exportfile = '{}-{}'.format(pubid, exportfile)

filepath = basedir + exportfile

model = ['publisher_id', 'article_doi', 'article_journal', 'article_title', 'article_type']

open_cassandra_connection()

ctr = 0

articles = PublishedArticle.objects.filter(publisher_id=pubid).limit(10000000)
with open(filepath, 'w', encoding='utf-8') as file:
    writer = csv.writer(file, delimiter='\t')
    writer.writerow(model)
    for article in articles:
        if article.article_journal == journal:
            row = []
            for col in model:
                row.append(article[col])
            writer.writerow(row)
            if toc:
                ctr += 1
                article.article_type = 'None'
                article.save()
                print("Updated %s articles" % (ctr,))

close_cassandra_connection()

