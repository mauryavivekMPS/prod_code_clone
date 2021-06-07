import sys
import os
import time
import csv
import re
from getopt import getopt
import traceback

os.sys.path.append(os.environ['IVETL_ROOT'])

from ivetl.models import ArticleCitations
from ivetl.celery import open_cassandra_connection, close_cassandra_connection

opts, args = getopt(sys.argv[1:], 'bhfl:p:so:e:u', [
    'brief',
    'help',
    'full',
    'limit',
    'publisher',
    'strip-newlines',
    'outfile',
    'exportfile',
    'unique'])

pubid = None
full_export = False
limit = None
exportfile = 'article_citations_export.tsv'
brief = False
strip_newlines = False
uniques_check = False

helptext = '''usage: python export_article_citations.py -- [ -b | -h | -f | -l limit ] -p publisher_id

Query the article_citations table in Cassandra and export values for analysis.

Environment variables:

This script uses the open_cassandra_connection and close_cassandra_connection
routines defined in celery.py, which in turn use variables defined in common.py.
The Cassandra IP list can be set with the following variable, e.g:

export IVETL_CASSANDRA_IP=bk-vizor-dev-01.highwire.org

Use a comma separated list for multiple hosts.

Options and arguments:
-b     :  brief format. only export essential columns ()
-f     :  full export. writes all rows
-h     :  print this help message and exit (also --help)
-l     :  limit value to use when querying cassandra. default: None (all records)
-o     :  output file path to write to. Default: /iv/working/misc/{publisher-id}-article_citations_export.tsv
-p     :  publisher_id value to use when querying cassandra.
-s     :  strip newlines from columns. Useful for post-processing with line-by-line unix tools, such as grep.
-u     :  verify uniques. Due to tombstones, failed compactions, etc.,
              it is possible to get output with multiple rows for the same primary key.
              This option will force a uniqueness check ensuring one row per unique key.
'''


basedir = '/iv/working/misc/'

for opt, val in opts:
    if opt in ('-h', '--help'):
        print(helptext)
        sys.exit()
    elif opt in  ('-f', '--full'):
        full_export = True
    elif opt == ('-l', '--limit'):
        l = val
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
    elif opt in ('-p', '--publisher'):
        pubid = val
        print('initializing single publisher run: %s' % pubid)
    elif opt in ('-s', '--strip-newlines'):
        strip_newlines = True
    elif opt in ('-o', '--output-file'):
        exportfile = val
        basedir = ''
        print('initializing output file: %s' % exportfile)
    elif opt in ('-b', '--brief'):
        brief = True
    elif opt in ('-u', '--unique'):
        print('running with uniqueness check...')
        uniques_check = True

if basedir == '/iv/working/misc/':
    exportfile = '{}-{}'.format(pubid, exportfile)

filepath = basedir + exportfile

# Q: Why is the model hardcoded below?
# A: Convenience. Also, it appears the cassandra Django driver doesn't
#    implement the function to "get all fields" from a model.
model = ['publisher_id', 'article_doi', 'citation_doi', 'citation_date',
    'citation_first_author', 'citation_issue', 'citation_journal_issn',
    'citation_journal_title', 'citation_pages',
    'citation_scopus_id','citation_sources',  'citation_source_scopus',
    'citation_source_xref', 'citation_title', 'citation_volume',
    'citation_count', 'created', 'updated', 'is_cohort']

if brief:
    model = ['publisher_id', 'article_doi', 'citation_doi', 'citation_date',
    'citation_journal_issn',
    'citation_journal_title','citation_scopus_id','citation_sources',
    'citation_source_scopus', 'citation_source_xref', 'citation_count',
    'created', 'updated']

open_cassandra_connection()

if pubid:
    articles = ArticleCitations.objects.filter(publisher_id=pubid).limit(limit)
else:
    articles = ArticleCitations.objects.all().limit(limit)


uniques_index = {}

with open(filepath, 'w', encoding='utf-8') as file:
    writer = csv.writer(file, delimiter='\t')
    writer.writerow(model)
    if uniques_check:
        for article in articles:
            publisher_id = re.sub(r'\W+', '', article['publisher_id'])
            article_doi = article['article_doi'].strip()
            citation_doi = article['citation_doi'].strip()
            article_key = publisher_id + article_doi + citation_doi
            if not article_key in uniques_index:
                uniques_index[article_key] = 0
            uniques_index[article_key] += 1
    for article in articles:
        row = []
        for col in model:
            # coerce truthy values to string, strip newlines.
            if col and strip_newlines:
                row.append(str(article[col]).replace('\n', ' '))
                continue
            row.append(article[col])
        if uniques_check:
            publisher_id = re.sub(r'\W+', '', article['publisher_id'])
            article_doi = article['article_doi'].strip()
            citation_doi = article['citation_doi'].strip()
            article_key = publisher_id + article_doi + citation_doi
            if uniques_index[article_key] > 1:
                uniques_index[article_key] -= 1
                continue
        writer.writerow(row)

close_cassandra_connection()
