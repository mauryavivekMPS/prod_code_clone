import sys
import os
import time
import csv
import re
from getopt import getopt
import traceback

os.sys.path.append(os.environ['IVETL_ROOT'])

from ivetl.models import PublisherMetadata
from ivetl.celery import open_cassandra_connection, close_cassandra_connection

opts, args = getopt(sys.argv[1:], 'hfl:p:o:e:', [
    'help',
    'full',
    'publisher',
    'outfile',
    'exportfile'])

pubid = None
full_export = False
limit = None
exportfile = 'publisher_reports_data_export.tsv'


helptext = '''usage: python export_publisher_reports_data.py -- [ -h | -p publisher_id | -o output file path ]

Query the publisher_metadata table in Cassandra and export report values for analysis.

Environment variables:

This script uses the open_cassandra_connection and close_cassandra_connection
routines defined in celery.py, which in turn use variables defined in common.py.
The Cassandra IP list can be set with the following variable, e.g:

export IVETL_CASSANDRA_IP=bk-vizor-dev-01.highwire.org

Use a comma separated list for multiple hosts.

Options and arguments:
-h     :  print this help message and exit (also --help)
-o     :  output file path to write to. Default: /iv/working/misc/{publisher-id}-publisher_reports_data_export.tsv
-p     :  publisher_id value to use when querying cassandra, limiting run to single publisher.
'''


basedir = '/iv/working/misc/'

for opt in opts:
    if opt[0] == '-h':
        print(helptext)
        sys.exit()
    if opt[0] == '-p':
        pubid = opt[1]
        print('initializing single publisher run: %s' % pubid)
    if opt[0] == '-o':
        exportfile = opt[1]
        basedir = ''
        print('initializing output file: %s' % exportfile)

if pubid and basedir == '/iv/working/misc/':
    exportfile = '{}-{}'.format(pubid, exportfile)

filepath = basedir + exportfile

pmodel = ['publisher_id', 'reports_username', 'reports_project',
    'reports_user_id', 'reports_password', 'reports_group_id', 'reports_project_id',
    'reports_setup_status']

open_cassandra_connection()

if pubid:
    publishers = PublisherMetadata.objects.filter(publisher_id=pubid)
else:
    publishers = PublisherMetadata.objects.all()

with open(filepath, 'w', encoding='utf-8') as file:
    writer = csv.writer(file, delimiter='\t')
    writer.writerow(pmodel)
    for publisher in publishers:
        row = []
        for col in pmodel:
            try:
                row.append(publisher[col])
            except KeyError as err:
                print('KeyError: %s, %s' % (col, publisher.publisher_id))
        writer.writerow(row)

close_cassandra_connection()
