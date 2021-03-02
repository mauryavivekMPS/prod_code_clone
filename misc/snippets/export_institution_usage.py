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

from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from ivetl.models import InstitutionUsageStat, InstitutionUsageStatComposite, SubscriptionPricing, ProductBundle
from ivetl.common import common
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl import utils

opts, args = getopt(sys.argv[1:], 'hl:p:s:c:', [
    'help',
    'limit',
    'publisher',
    'stat-exportfile',
    'composite-exportfile'])

helptext = '''usage: python export_institution_usage.py -- [ -h  | -l limit |  -c composite-exportfile | -s stat-exportfile | -f from-date | -t to-date ] -p publisher-id

Query the insitution_usage_stat and/or instiution_usage_stat_composite tables in Cassandra and export values for analysis.
Originally developed for testing, troubleshooting and resolving VIZOR-334,
"UpdateInstitutionUsageStatsTask cassandra "ALLOW FILTERING" exception"

Environment variables:

This script uses the open_cassandra_connection and close_cassandra_connection
routines defined in celery.py, which in turn use variables defined in common.py.
The Cassandra IP list can be set with the following variable, e.g:

export IVETL_CASSANDRA_IP=bk-vizor-dev-01.highwire.org

Use a comma separated list for multiple hosts.

Options and arguments:
-h     :  print this help message and exit (also --help)
-l     :  limit value to use when querying cassandra. default: None (all records)
-s     :  institution_stat output file path to write to. Default: /iv/working/misc/{publisher_id}-institution_stat_export.tsv
-t     :  institution_stat_composite output file path to write to. Default: /iv/working/misc/{publisher_id}-institution_stat_composite_export.tsv
-p     :  publisher_id value to use when querying cassandra. required.
-f     :  from_date to use for CQL query generation. Default: 2020-08-01
-t     :  to_date to use for CQL query generation. Default: 2020-08-31
'''


basedir = '/iv/working/misc/'
publisher_id = None
limit = None
stat_exportfile = 'institution_stat_export.tsv'
composite_exportfile = 'institution_stat_composite_export.tsv'
from_date = datetime.strptime('2020-04-01', '%Y-%m-%d')
to_date = datetime.strptime('2020-04-30', '%Y-%m-%d')

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
    elif opt[0] == '-s':
        stat_exportfile = opt[1]
        basedir = ''
        print('initializing stat output file: %s' % status_exportfile)
    elif opt[0] == '-c':
        composite_exportfile = opt[1]
        basedir = ''

if basedir == '/iv/working/misc/':
    status_exportfile = '{}-{}'.format(publisher_id, stat_exportfile)
    task_exportfile = '{}-{}'.format(publisher_id, composite_exportfile)

sfilepath = basedir + status_exportfile
cfilepath = basedir + task_exportfile

# model has same fields for both
model = ['publisher_id', 'counter_type', 'journal', 'subscriber_id',
    'usage_date', 'usage_category', 'journal_print_issn',
    'journal_online_issn',
    'institution_name',  'usage', 'bundle_name',
    'amount', 'trial',
    'trial_expiration_date']

inst_stats = []
inst_stat_composites = []

print('Connecting to cassandra...')
print(common.CASSANDRA_IP_LIST)
open_cassandra_connection()
cluster = Cluster(common.CASSANDRA_IP_LIST)
session = cluster.connect()

with open(sfilepath, 'w',
    encoding='utf-8') as sfile, open(cfilepath, 'w',
    encoding='utf-8') as cfile:
    swriter = csv.writer(sfile, delimiter='\t')
    swriter.writerow(model)
    cwriter = csv.writer(cfile, delimiter='\t')
    cwriter.writerow(model)
    publisher_stats_sql = """
        select *
        from impactvizor.institution_usage_stat
        where publisher_id = %s
        limit 100000000
    """

    publisher_stats_statement = SimpleStatement(publisher_stats_sql, fetch_size=1000)

    # , 'jr3', date,
    for stat in session.execute(publisher_stats_statement, (publisher_id,)):
        row = []
        for col in model:
            try:
                row.append(getattr(stat, col))
            except AttributeError:
                print(AttributeError)
                row.append('Not Queried')
        swriter.writerow(row)            # get subscriptions for this pub and year
    # todo: rework to use correct partition key
    composite_stats_sql = """
        select *
        from impactvizor.institution_usage_stat_composite
        where publisher_id = %s
        limit 100000000
    """

    #composite_stats_statement = SimpleStatement(composite_stats_sql, fetch_size=1000)

    #for stat in session.execute(composite_stats_statement, (publisher_id,)):
    #    row = []
    #    for col in model:
    #        try:
    #            row.append(getattr(stat, col))
    #        except AttributeError:
    #            print(AttributeError)
    #            row.append('Not Queried')
    #    cwriter.writerow(row)

close_cassandra_connection()

elapsed = datetime.now() - start
print('elapsed time: {}'.format(elapsed))
