import sys
import os
import time
import csv
import re
from getopt import getopt
import traceback

os.sys.path.append(os.environ['IVETL_ROOT'])

from ivetl.models import PublishedArticleValues
from ivetl.celery import open_cassandra_connection, close_cassandra_connection

opts, args = getopt(sys.argv[1:], 'hfl:p:so:e:', [
    'help',
    'full',
    'limit',
    'publisher',
    'strip-newlines',
    'outfile',
    'exportfile'])

pubid = None
full_export = False
limit = None
exportfile = 'published_article_values_export.tsv'
strip_newlines = False


helptext = '''usage: python export_published_article_values.py -- [ -h | -f | -l limit ] -p publisher_id

Query the published_article_values table in Cassandra and export values for analysis.

Environment variables:

This script uses the open_cassandra_connection and close_cassandra_connection
routines defined in celery.py, which in turn use variables defined in common.py.
The Cassandra IP list can be set with the following variable, e.g:

export IVETL_CASSANDRA_IP=bk-vizor-dev-01.highwire.org

Use a comma separated list for multiple hosts.

Options and arguments:
-f     :  full export. writes all rows
-h     :  print this help message and exit (also --help)
-l     :  limit value to use when querying cassandra. default: None (all records)
-o     :  output file path to write to. Default: /iv/working/misc/{publisher-id}-rejected_article_export.tsv
-p     :  publisher_id value to use when querying cassandra. required.
-s     :  strip newlines from columns. Useful for post-processing with line-by-line unix tools, such as grep.
'''


basedir = '/iv/working/misc/'

for opt in opts:
    if opt[0] == '-h':
        print(helptext)
        sys.exit()
    if opt[0] == '-f':
        full_export = True
    if opt[0] == '-l':
        l = opt[1]
        if l == 'None' or l == 'none':
            limit = None
        elif type(l) is str:
            try:
                limit = int(l)
            except:
                print('Failed to parse limit value to int: %s' % l)
                sys.exit()
        else:
            limit = l
    if opt[0] == '-p':
        pubid = opt[1]
        print('initializing single publisher run: %s' % pubid)
    elif opt in ('-s', '--strip-newlines'):
        strip_newlines = True
    if opt[0] == '-o':
        exportfile = opt[1]
        basedir = ''
        print('initializing output file: %s' % exportfile)

if basedir == '/iv/working/misc/':
    exportfile = '{}-{}'.format(pubid, exportfile)

filepath = basedir + exportfile

model = ['publisher_id', 'article_doi', 'source', 'name', 'value_text']

open_cassandra_connection()

articles = PublishedArticleValues.objects.filter(publisher_id=pubid).limit(limit)

with open(filepath, 'w', encoding='utf-8') as file:
    writer = csv.writer(file, delimiter='\t')
    writer.writerow(model)
    for article in articles:
        row = []
        for col in model:
            # coerce truthy values to string, strip newlines.
            if col and strip_newlines:
                row.append(str(article[col]).replace('\n', ' '))
                continue
            row.append(article[col])
        writer.writerow(row)

close_cassandra_connection()
