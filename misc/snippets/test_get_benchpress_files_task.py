import sys
import os
import time
import csv
import re
import shutil
from getopt import getopt
import datetime
from dateutil.parser import parse
import traceback

os.sys.path.append(os.environ['IVETL_ROOT'])

from ivetl.common import common
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.models import PublisherJournal
from ivetl import utils

start = datetime.datetime.now()

from ivetl.models import ArticleCitations
from ivetl.celery import open_cassandra_connection, close_cassandra_connection

opts, args = getopt(sys.argv[1:], 'hp:f:t:', [
    'help',
    'publisher',
    'from-date',
    'to-date',
    ])

publisher_id = None

helptext = '''usage: python test_get_benchpress_files_task.py -- [ -h ] -p publisher_id -f from_date -t to_date
Test the get_benchpress_files_task
Code is manually copied / pasted over for isolation and easy script testing outside of task / pipeline environment

Environment variables:
This script uses the open_cassandra_connection and close_cassandra_connection
routines defined in celery.py, which in turn use variables defined in common.py.
The Cassandra IP list can be set with the following variable, e.g:
export IVETL_CASSANDRA_IP=bk-vizor-dev-01.highwire.org
Use a comma separated list for multiple hosts.
Options and arguments:
-h     :  print this help message and exit (also --help)
-p     :  publisher_id value to use when querying cassandra. required.
-f     :  from_date
-t     :  to_date
'''

work_folder = '/iv/working/misc/'

for opt in opts:
    if opt[0] == '-h':
        print(helptext)
        sys.exit()
    if opt[0] == '-t':
        to_date = opt[1]
    if opt[0] == '-p':
        publisher_id = opt[1]
        print('initializing single publisher run: %s' % publisher_id)
    if opt[0] == '-f':
        from_date = opt[1]

def from_json_date(s):
    if s:
        return parse(s).date()
    else:
        return None

def to_json_datetime(d):
    if d:
        return d.isoformat()
    else:
        return None

def from_json_datetime(s):
    if s:
        return parse(s)
    else:
        return None

open_cassandra_connection()

# publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args

product_id = 'bp-test'
pipeline_id = 'bp-test'
job_id = 'manual-test-run'

BUCKET = common.BENCHPRESS_BUCKET

from_date = from_json_date(from_date)
to_date = from_json_date(to_date)

today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)

if from_date:
    from_date = datetime.datetime.combine(from_date, datetime.time.min)

if to_date:
    to_date = datetime.datetime.combine(to_date, datetime.time.min)

def _previous_quarter(ref):
    if ref.month < 4:
        return datetime.datetime(ref.year - 1, 10, 1), datetime.datetime(ref.year - 1, 12, 31)
    elif ref.month < 7:
        return datetime.datetime(ref.year, 1, 1), datetime.datetime(ref.year, 3, 31)
    elif ref.month < 10:
        return datetime.datetime(ref.year, 4, 1), datetime.datetime(ref.year, 6, 30)
    else:
        return datetime.datetime(ref.year, 7, 1), datetime.datetime(ref.year, 9, 30)

if not (from_date or to_date):
    from_date, to_date = _previous_quarter(today)

if from_date > today - datetime.timedelta(1):
    tlogger.error('Invalid date range: The from date must be before yesterday.')
    raise Exception

if not to_date:
    to_date = today - datetime.timedelta(1)

if to_date < from_date:
    tlogger.error('Invalid date range: The date range must be at least one day.')
    raise Exception

print('Using date range: %s to %s' % (from_date.strftime('%Y-%m-%d'), to_date.strftime('%Y-%m-%d')))
from_strf = from_date.strftime('%m_%d_%Y')
to_strf = to_date.strftime('%m_%d_%Y')

journals_with_benchpress = [p.journal_code for p in PublisherJournal.objects.filter(
    publisher_id=publisher_id,
    product_id='published_articles',
    use_benchpress=True
)]

total_count = len(journals_with_benchpress)
print(publisher_id, product_id, pipeline_id, job_id, total_count)

files = []
count = 0

if journals_with_benchpress:
    for journal_code in journals_with_benchpress:

        print('Looking for file for journal: %s' % journal_code)

        j_file_name = '%s_%s_%s.txt' % (journal_code, from_strf, to_strf)
        print('Using filename: %s' % j_file_name)

        try:
            dl_file_path = utils.download_file_from_s3(BUCKET, j_file_name)
            print('Retrieved file: %s' % dl_file_path)
            local_file_path = os.path.join(work_folder, j_file_name)
        except Exception as e:
            print('Failed to retrieve file: %s' % j_file_name)
            print(e)
            continue

        with open(local_file_path,
        'wb') as local_file, open(dl_file_path,
        'rb') as dl_file:
            shutil.copyfileobj(dl_file, local_file)

        files.append(local_file_path)

close_cassandra_connection()

print(files)
