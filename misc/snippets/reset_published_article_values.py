# !/usr/bin/env python
import sys
import os
import csv
from getopt import getopt

os.sys.path.append(os.environ['IVETL_ROOT'])

from ivetl.common import common
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.models import PublishedArticleValues

opts, args = getopt(sys.argv[1:], 'hdp:o:s:n:', [
    'help',
    'dryrun',
    'publisher',
    'outfile',
    'source',
    'name'])

publisher_id = None
source = None
name = None
dryrun = False
pavfile = 'published_article_value_deletes.tsv'

helptext = '''usage: python reset_published_article_values.py -- [ -h ] -p publisher_id -j article_journal
Query the published_article_values table in Cassandra, and delete rows that
match the provided source / name (e.g. custom / article_type).

Useful for undoing problematic article_types introduced by a publisher FOAM file.

Environment variables:
This script uses the open_cassandra_connection and close_cassandra_connection
routines defined in celery.py, which in turn use variables defined in common.py.
The Cassandra IP list can be set with the following variable, e.g:
export IVETL_CASSANDRA_IP=bk-vizor-dev-01.highwire.org
Use a comma separated list for multiple hosts.
Options and arguments:
-d     :  dryrun: match and export values, but do not delete rows from cassandra.
-h     :  print this help message and exit (also --help)
-n     :  set value to match for the name column in published_article_values. required.
-o     :  output file path to write to. Default: /iv/working/misc/{publisher-id}-published_article_value_deletes.tsv
-p     :  publisher_id value to use when querying cassandra. required.
-s     :  set value to match source column in published_article_values. required.
'''

basedir = '/iv/working/misc/'

for opt in opts:
    if opt[0] == '-h':
        print(helptext)
        sys.exit()
    if opt[0] == '-d':
        print('dryrun: no rows will be deleted.')
        dryrun = True
    if opt[0] == '-p':
        publisher_id = opt[1]
        print('initializing single publisher run: %s' % publisher_id)
    if opt[0] == '-n':
        name = opt[1]
        print('initializing name value: %s' % name)
    if opt[0] == '-s':
        source = opt[1]
        print('initializing source value: %s' % source)
    if opt[0] == '-o':
        exportfile = opt[1]
        basedir = ''
        print('initializing output file: %s' % exportfile)

if basedir == '/iv/working/misc/':
    pavfile = '{}-{}'.format(publisher_id, pavfile)

pav_filepath = basedir + pavfile

pav_model = ['publisher_id', 'article_doi', 'source', 'name', 'value_text']

exit_msg = []

if not publisher_id:
    exit_msg.append('publisher_id (-p) is a required paramter.\n')
if not source:
    exit_msg.append('source (-s) is a required paramter.\n')
if not name:
    exit_msg.append('name (-n) is a required paramter.\n')

if len(exit_msg) > 0:
    exit_msg.append('See --help for more details.\n')
    print(''.join(exit_msg))
    sys.exit()

open_cassandra_connection()
ctr = 0
matched = 0
modified = 0
values = PublishedArticleValues.objects.filter(publisher_id=publisher_id).limit(10000000)
with open(pav_filepath, 'w', encoding='utf-8') as vfile:
    vwriter = csv.writer(vfile, delimiter='\t')
    vwriter.writerow(pav_model)
    for pa_value in values:
        ctr += 1
        if pa_value['source'] != source or pa_value['name'] != name:
            continue
        matched += 1
        try:
            pa_value_row = []
            for col in pav_model:
                pa_value_row.append(pa_value[col])
            vwriter.writerow(pa_value_row)
            if not dryrun:
                modified += 1
                pa_value.delete()
        except Exception as e:
            print('Failed to write / delete PublishedArticleValue: ', e)
    print("Scanned %s published_article_values" % (ctr,))
    print('Matched %s rows' % (matched,))
    print("Deleted %s published_article_values rows" % (modified,))

close_cassandra_connection()
