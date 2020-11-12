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

opts, args = getopt(sys.argv[1:], 'hl:p:f:t:s:r', [
    'help',
    'limit',
    'publisher',
    'from-date',
    'to-date',
    'stat-exportfile',
    'read-only'
    ])

helptext = '''usage: python update_institution_stats_manual.py -- [ -h  | -l limit |  -c composite-exportfile | -s stat-exportfile | -f from-date | -t to-date ] -p publisher-id

Utility script for surgical application of the ivetl/pipelines/productbundles/tasks/update_institution_usage_stats code
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
-f     :  from_date to use for CQL query generation. YYYY-MM-DD. Default: 2020-08-01
-l     :  limit value to use when querying cassandra. default: None (all records)
-p     :  publisher_id value to use when querying cassandra. required.
-r     :  read only, dry run. Skip updates in database, but still write them to output file for analysis. Default: False
-s     :  institution_stat output file path to write to. Writes rows which met criteria for update. Default: /iv/working/misc/{publisher_id}-institution_stat_updates.tsv
-t     :  to_date to use for CQL query generation. YYYY-MM-DD. Default: Current date.
'''


basedir = '/iv/working/misc/'
publisher_id = None
limit = None
stat_exportfile = 'institution_stat_updates.tsv'
from_date = datetime(2020, 8, 1)
now = datetime.now()
to_date = datetime(now.year, now.month, 1)
read_only = False
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
    elif opt[0] == '-f':
        from_date = datetime.strptime(opt[1], '%Y-%m-%d')
    elif opt[0] == '-t':
        to_date = datetime.strptime(opt[1], '%Y-%m-%d')
    elif opt[0] == '-r':
        read_only = True

if basedir == '/iv/working/misc/':
    stat_exportfile = '{}-{}'.format(publisher_id, stat_exportfile)

sfilepath = basedir + stat_exportfile

model = ['publisher_id', 'counter_type', 'journal', 'subscriber_id',
    'usage_date', 'usage_category', 'journal_print_issn',
    'journal_online_issn',
    'institution_name',  'usage', 'bundle_name',
    'amount', 'trial',
    'trial_expiration_date']
match_fields = ['bundle_name', 'amount', 'trial', 'trial_expiration_date']
header = ['publisher_id', 'counter_type', 'journal', 'subscriber_id',
    'usage_date', 'usage_category', 'journal_print_issn',
    'journal_online_issn',
    'institution_name',  'usage', 'bundle_name',
    'amount', 'trial',
    'trial_expiration_date', 'updated_bundle_name', 'updated_amount',
    'updated_trial', 'update_trial_expiration_date']

print('Initializing update, from %s to %s' % (from_date, to_date))
print('Connecting to cassandra...')
print(common.CASSANDRA_IP_LIST)
open_cassandra_connection()
cluster = Cluster(common.CASSANDRA_IP_LIST)
session = cluster.connect()

with open(sfilepath, 'w',
    encoding='utf-8') as sfile:
    swriter = csv.writer(sfile, delimiter='\t')
    swriter.writerow(header)
    count = 0

    month_index = []
    for date in utils.month_range(from_date, to_date):
        month_index.append(date)
# 100000000
    publisher_stats_sql = """
      select counter_type, subscriber_id, journal, usage_category, usage_date,
      journal_print_issn, journal_online_issn, institution_name,
      bundle_name, amount, trial, trial_expiration_date
      from impactvizor.institution_usage_stat
      where publisher_id = %s
      limit 900000
    """

    publisher_stats_statement = SimpleStatement(publisher_stats_sql, fetch_size=1000)

    for stat in session.execute(publisher_stats_statement, (publisher_id,)):
        # a very non-ideal way to filter out in code,
        # rather than via db query, to avoid Cassandra timeout issues
        # VIZOR-334
        if stat.counter_type != 'jr3' or stat.usage_date not in month_index:
            continue

        count += 1
        row = []
        for col in model:
            try:
                row.append(getattr(stat, col))
            except AttributeError:
                row.append('Not Queried')

        # get subscriptions for this pub and year
        matching_subscriptions = SubscriptionPricing.objects.filter(
            publisher_id=publisher_id,
            membership_no=stat.subscriber_id,
            year=stat.usage_date.year,
        )

        # find one with a matching ISSN
        match = None
        for subscription in matching_subscriptions:
            try:
                bundle = ProductBundle.objects.get(
                    publisher_id=publisher_id,
                    bundle_name=subscription.bundle_name,
                )

                issns = bundle.journal_issns
                if stat.journal_print_issn in issns or stat.journal_online_issn in issns:
                    match = subscription
                    break

            except ProductBundle.DoesNotExist:
                pass

        if match:
            for field in match_fields:
                try:
                    row.append(getattr(match, field))
                except AttributeError:
                    row.append('Not Found')
            if not read_only:
                InstitutionUsageStat.objects(
                    publisher_id=publisher_id,
                    counter_type='jr3',
                    journal=stat.journal,
                    subscriber_id=stat.subscriber_id,
                    usage_date=stat.usage_date,
                    usage_category=stat.usage_category,
                ).update(
                    bundle_name=match.bundle_name,
                    trial=match.trial,
                    trial_expiration_date=match.trial_expiration_date,
                    amount=match.amount,
                )

                # Note: we may in the future need to insert duplicate rows here if we end up supporting multiple matching bundles

                InstitutionUsageStatComposite.objects(
                    publisher_id=publisher_id,
                    counter_type='jr3',
                    journal=stat.journal,
                    subscriber_id=stat.subscriber_id,
                    usage_date=stat.usage_date,
                    usage_category=stat.usage_category,
                ).update(
                    bundle_name=match.bundle_name,
                    trial=match.trial,
                    trial_expiration_date=match.trial_expiration_date,
                    amount=match.amount,
                )
        else:
            row += ['No Match', 'No Match', 'No Match', 'No Match']
        swriter.writerow(row)
        
close_cassandra_connection()

elapsed = datetime.now() - start
print('elapsed time: %s' % (elapsed))
print('updated records: %s' % count)
