import sys
import os
import time
import csv
import re
from getopt import getopt
from datetime import datetime
import traceback

os.sys.path.append(os.environ['IVETL_ROOT'])

start = datetime.now()

from ivetl.models import RejectedArticles
from ivetl.celery import open_cassandra_connection, close_cassandra_connection

opts, args = getopt(sys.argv[1:], 'hfl:p:o:e:', [
    'help',
    'full',
    'limit',
    'publisher',
    'outfile',
    'exportfile'])

pubid = None
full_export = False
limit = None
exportfile = 'rejected_article_export.tsv'


helptext = '''usage: python export_rejected_articles.py -- [ -h | -f | -l limit ] -p publisher_id

Query the rejected_articles table in Cassandra and export values for analysis.

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
    if opt[0] == '-o':
        exportfile = opt[1]
        basedir = ''
        print('initializing output file: %s' % exportfile)

if basedir == '/iv/working/misc/':
    exportfile = '{}-{}'.format(pubid, exportfile)

filepath = basedir + exportfile

ramodel = ['publisher_id', 'manuscript_id', 'crossref_doi', 'status',
    'authors_match_score', 'crossref_match_score', 'citation_lookup_status',
    'citations',
    'manuscript_title',  'reject_reason', 'article_type',
    'date_of_publication', 'date_of_rejection',
    'published_journal', 'published_journal_issn',
    'published_publisher', 'published_title',
    'scopus_doi_status', 'scopus_id', 'source_file_name',
    'submitted_journal',  'preprint_doi',
    'editor', 'published_co_authors',
    'published_first_author', 'first_author', 'co_authors',
    'corresponding_author', 'created', 'updated', 'subject_category',
    'keywords', 'mendeley_saves', 'custom', 'custom_2', 'custom_3',
    'rejected_article_id']

open_cassandra_connection()

rarticles = RejectedArticles.objects.filter(publisher_id=pubid).limit(limit)

with open(filepath, 'w', encoding='utf-8') as file:
    writer = csv.writer(file, delimiter='\t')
    writer.writerow(ramodel)
    for rarticle in rarticles:
        row = []
        for col in ramodel:
            row.append(rarticle[col])
        writer.writerow(row)

close_cassandra_connection()

elapsed = datetime.now() - start
print('elapsed time: {}'.format(elapsed))
