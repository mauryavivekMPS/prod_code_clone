import sys
import os
import time
import csv
import re
from getopt import getopt
import traceback

os.sys.path.append(os.environ['IVETL_ROOT'])

from ivetl.models import PublishedArticle
from ivetl.celery import open_cassandra_connection, close_cassandra_connection

opts, args = getopt(sys.argv[1:], 'bhfl:p:o:e:', [
    'brief',
    'help',
    'full',
    'limit',
    'publisher',
    'outfile',
    'exportfile'])

pubid = None
full_export = False
limit = None
exportfile = 'published_article_export.tsv'
brief = False

helptext = '''usage: python export_published_articles.py -- [ -b | -h | -f | -l limit ] -p publisher_id

Query the published_article table in Cassandra and export values for analysis.

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
-o     :  output file path to write to. Default: /iv/working/misc/{publisher-id}-rejected_article_export.tsv
-p     :  publisher_id value to use when querying cassandra. required.
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
    elif opt in ('-o', '--output-file'):
        exportfile = val
        basedir = ''
        print('initializing output file: %s' % exportfile)
    elif opt in ('-b', '--brief'):
        brief = True

if basedir == '/iv/working/misc/':
    exportfile = '{}-{}'.format(pubid, exportfile)

filepath = basedir + exportfile

# Q: Why is the model hardcoded below?
# A: Convenience. Also, it appears the cassandra Django driver doesn't
#    implement the function to "get all fields" from a model.
model = ['publisher_id', 'article_doi', 'article_issue', 'article_journal',
    'article_journal_issn', 'article_pages', 'article_publisher',
    'article_scopus_id', 'article_title', 'article_type', 'article_volume',
    'citations_lookup_error', 'citations_updated_on', 'co_authors', 'created',
    'custom', 'custom_2', 'custom_3', 'date_of_publication',
    'date_of_rejection', 'editor', 'first_author', 'from_rejected_manuscript',
    'has_abstract', 'hw_metadata_retrieved', 'is_cohort', 'is_open_access',
    'rejected_manuscript_editor', 'rejected_manuscript_id',
    'scopus_citation_count', 'scopus_subtype', 'subject_category',
    'month_usage_03', 'month_usage_06', 'month_usage_09', 'month_usage_12',
    'month_usage_24', 'month_usage_36', 'month_usage_48', 'month_usage_60',
    'month_usage_full_03', 'month_usage_full_06', 'month_usage_full_09',
    'month_usage_full_12', 'month_usage_full_24', 'month_usage_full_36',
    'month_usage_full_48', 'month_usage_full_60', 'month_usage_pdf_03',
    'month_usage_pdf_06', 'month_usage_pdf_09', 'month_usage_pdf_12',
    'month_usage_pdf_24', 'month_usage_pdf_36', 'month_usage_pdf_48',
    'month_usage_pdf_60', 'month_usage_abstract_03', 'month_usage_abstract_06',
    'month_usage_abstract_09', 'month_usage_abstract_12',
    'month_usage_abstract_24', 'month_usage_abstract_36',
    'month_usage_abstract_48', 'month_usage_abstract_60', 'usage_start_date',
    'mendeley_saves', 'altmetrics_facebook', 'altmetrics_blogs',
    'altmetrics_twitter', 'altmetrics_gplus', 'altmetrics_news_outlets',
    'altmetrics_wikipedia', 'altmetrics_video', 'altmetrics_policy_docs',
    'altmetrics_reddit', 'f1000_total_score', 'f1000_num_recommendations',
    'f1000_average_score', 'meta_pmid', 'meta_actual_ef',
    'meta_actual_citation_count', 'meta_predicted_ef',
    'meta_predicted_citation_count', 'meta_top_1', 'meta_top_5',
    'meta_top_10', 'meta_top_25', 'meta_top_50', 'meta_predicted_tiers',
    'meta_actual_tiers', 'previous_citation_count', 'citation_count',
    'is_tr_citable', 'updated']

if brief:
    model = ['publisher_id', 'article_doi', 'article_journal',
        'article_journal_issn', 'article_scopus_id', 'article_title',
        'article_type', 'created', 'date_of_publication', 'is_cohort',
        'scopus_citation_count', 'citation_count', 'updated']

open_cassandra_connection()

articles = PublishedArticle.objects.filter(publisher_id=pubid).limit(limit)

with open(filepath, 'w', encoding='utf-8') as file:
    writer = csv.writer(file, delimiter='\t')
    writer.writerow(model)
    for article in articles:
        row = []
        for col in model:
            row.append(article[col])
        writer.writerow(row)

close_cassandra_connection()
