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

from ivetl.models import PipelineStatus, PipelineTaskStatus
from ivetl.celery import open_cassandra_connection, close_cassandra_connection

opts, args = getopt(sys.argv[1:], 'hl:j:i:d:p:s:t:', [
    'help',
    'limit',
    'job-id',
    'pipeline',
    'product',
    'publisher',
    'status-exportfile',
    'task-exportfile'])

helptext = '''usage: python export_pipeline_data.py -- [ -h  | -l limit | -j job-id | -i pipeline | -d product | -p publisher_id | -s status-exportfile | -t task-exportfile ]

Query the pipeline_status and/or pipeline_task_status tables in Cassandra and export values for analysis.

Environment variables:

This script uses the open_cassandra_connection and close_cassandra_connection
routines defined in celery.py, which in turn use variables defined in common.py.
The Cassandra IP list can be set with the following variable, e.g:

export IVETL_CASSANDRA_IP=bk-vizor-dev-01.highwire.org

Use a comma separated list for multiple hosts.

Options and arguments:
-h     :  print this help message and exit (also --help)
-d     :  limit query by product_id. default: None (all products)
-j     :  limit query by job_id. default: None (all jobs)
-i     :  limit query by pipeline_id. default: None (all pipelines)
-l     :  limit value to use when querying cassandra. default: None (all records)
-s     :  pipeline_status output file path to write to. Default: /iv/working/misc/{YYYY-MM-DD}-pipeline_status_export.tsv
-t     :  pipeline_task_status output file path to write to. Default: /iv/working/misc/{YYYY-MM-DD}-pipeline_task_status_export.tsv
-p     :  publisher_id value to use when querying cassandra. default: None (all publishers).
'''


basedir = '/iv/working/misc/'
publisher_id = None
product_id = None
job_id = None
pipeline_id = None
limit = None
status_exportfile = 'pipeline_status_export.tsv'
task_exportfile = 'pipeline_task_status_export.tsv'


for opt in opts:
    if opt[0] == '-h':
        print(helptext)
        sys.exit()
    elif opt[0] == '-l':
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
    elif opt[0] == '-p':
        publisher_id = opt[1]
        print('initializing single publisher run: %s' % publisher_id)
    elif opt[0] == '-d':
        productid = opt[1]
    elif opt[0] == '-j':
        jobid = opt[1]
    elif opt[0] == '-i':
        pipeline_id = opt[1]
    elif opt[0] == '-s':
        status_exportfile = opt[1]
        basedir = ''
        print('initializing status output file: %s' % status_exportfile)
    elif opt[0] == '-t':
        task_exportfile = opt[1]
        basedir = ''

if basedir == '/iv/working/misc/':
    status_exportfile = '{}-{}'.format(publisher_id, status_exportfile)
    task_exportfile = '{}-{}'.format(publisher_id, task_exportfile)

sfilepath = basedir + status_exportfile
tfilepath = basedir + task_exportfile

psmodel = ['publisher_id', 'product_id', 'pipeline_id', 'job_id',
    'current_task', 'current_task_count', 'total_task_count',
    'duration_seconds',
    'end_time',  'error_details', 'start_time',
    'status', 'updated',
    'workfolder', 'user_email',
    'params_json', 'stop_instruction']

ptsmodel = ['publisher_id', 'product_id', 'pipeline_id', 'job_id',
    'task_id', 'duration_seconds',
    'current_record_count',  'total_record_count', 'end_time',
    'error_details', 'start_time',
    'status', 'updated',
    'task_args_json', 'workfolder']

open_cassandra_connection()

pipeline_task_statuses = []

if not publisher_id:
    pipeline_statuses = PipelineStatus.objects.all()
    # pipeline_task_statuses = PipelineTaskStatus.objects.limit(limit)
else:
    pipeline_statuses = PipelineStatus.objects.filter(publisher_id=publisher_id)
    pipeline_task_statuses = PipelineTaskStatus.objects.filter(publisher_id=publisher_id)

with open(sfilepath, 'w',
    encoding='utf-8') as sfile, open(tfilepath, 'w',
    encoding='utf-8') as tfile:
    swriter = csv.writer(sfile, delimiter='\t')
    swriter.writerow(psmodel)
    twriter = csv.writer(tfile, delimiter='\t')
    twriter.writerow(ptsmodel)
    for status in pipeline_statuses:
        row = []
        for col in psmodel:
            try:
                row.append(status[col])
            except:
                row.append('Error: Field Missing')
        swriter.writerow(row)
    for task in pipeline_task_statuses:
        row = []
        for col in ptsmodel:
            row.append(task[col])
        twriter.writerow(row)

close_cassandra_connection()

elapsed = datetime.now() - start
print('elapsed time: {}'.format(elapsed))
