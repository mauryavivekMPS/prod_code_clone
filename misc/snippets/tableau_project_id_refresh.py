import sys
import os
import time
from getopt import getopt
import traceback
import logging

os.sys.path.append(os.environ['IVETL_ROOT'])

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    filename=os.path.join( os.environ.get('IVWEB_LOG_ROOT', '/var/log/ivweb/'), 'tableau-connector-manual.log'),
    filemode='a',
)

from ivetl.common import common
from ivetl.models import PublisherMetadata
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.connectors import TableauConnector

opts, args = getopt(sys.argv[1:], 'hp:', ['help', 'publisher'])

# single publisher vs all
pubid = None

helptext = '''usage: python tableau_project_id_refresh.py -- [ -h | -p publisher_id ]

Environment variables:

This script uses the open_cassandra_connection and close_cassandra_connection
routines defined in celery.py, which in turn use variables defined in common.py.
The Cassandra IP list can be set with the following variable, e.g:

export IVETL_CASSANDRA_IP=bk-vizor-dev-01.highwire.org

Use a comma separated list for multiple hosts.

This script also connects to a Tableau Server instance.
Set the Tableau instance with the following environment variables:

export IVETL_TABLEAU_SERVER=bk-vizor-win-dev-01.highwire.org

e.g. for dev or

export IVETL_TABLEAU_SERVER=reports-data.vizors.org

for the production instance running 2019.4+.

Options and arguments:
-h     :  print this help message and exit (also --help)
-o     :  output file path to write to. Default: /iv/working/misc/{publisher-id}-publisher_reports_data_export.tsv
-p     :  publisher_id value to use when querying cassandra, limiting run to single publisher.

This script can be used to sync up a Cassandra instance with a Tableau Server instance.
Examples of use include when switching a local environment
from a shared development Tableau Server
to a production or local Tableau Server instance, or when upgrading or
switching out one production Tableau Server instance for another.

The script will query a Tableau Server instance and a Cassandra instance,
comparing the reports_project_id, reports_group_id, and reports_user_id
values. It will update the Cassandra PublisherMetadata table with the values
received from Tableau if there is a mismatch.

The script keys the Tableau Server IDs off the human readable names, and
these must match up between environments:

Tableau Project Name (e.g. 'AAAS')
Tableau Group Name (e.g. 'AAAS')
Tableau User Name (e.g. 'aaas')

As an example, if the Cassandra instance you are updating stores the value
'8c549bc8-d259-47d2-bfb3-12a532213856' for the AAAS project id, and the
Tableau Server instance has created the AAAS project with the id '0677c734-b5b4-4eac-a796-0536c5e8b601',
then the Tableau Server version will be written to the Cassandra instance.

If the IDs all match for a given publisher, no update will be written for that publisher.
This means once the script has run once, assuming the Cassandra database doesn't change,
it will result in all no-ops.

The script writes output to stdout using python's print() facility.
'''

for opt in opts:
    if opt[0] == '-p':
        pubid = opt[1]
        logging.info('initializing single publisher run: %s' % pubid)
    if opt[0] == '-h':
        print(helptext)
        sys.exit()

t = TableauConnector(
    username=common.TABLEAU_USERNAME,
    password=common.TABLEAU_PASSWORD,
    server=common.TABLEAU_SERVER
)

projects = t.list_projects()
groups = t.list_groups()
users = t.list_users()

pidx = {}
gidx = {}
uidx = {}

for project in projects:
    pidx[project['name']] = project['id']

for group in groups:
    gidx[group['name']] = group['id']

for user in users:
    uidx[user['name']] = user['id']

update_count = 0
noop_count = 0

open_cassandra_connection()

if pubid:
    publishers = PublisherMetadata.objects.filter(publisher_id=pubid)
else:
    publishers = PublisherMetadata.objects.all()
    print('running all publishers')

for publisher in publishers:
    noop = True
    if publisher.publisher_id == 'hw':
        logging.info('skipping special-case hw publisher record')
        continue
    updates = {}
    project_name = publisher.reports_project
    print(project_name)
    group_name = '%s User Group' % project_name
    print(group_name)
    user_name = publisher.reports_username
    print(user_name)
    project_id = publisher.reports_project_id
    print(project_id)
    group_id = publisher.reports_group_id
    user_id = publisher.reports_user_id
    if project_name in pidx and project_id != pidx[project_name]:
        noop = False
        project_id = pidx[project_name]
    else:
        print('noop:')
        print(project_name)
        print(project_name in pidx)
        print(project_id)
    if group_name in gidx and group_id != gidx[group_name]:
        noop = False
        group_id = gidx[group_name]
    if user_name in uidx and user_id != uidx[user_name]:
        noop = False
        user_id = uidx[user_name]
    if not noop:
        update_count += 1
        print('Updates needed for publisher: %s' % publisher.publisher_id)
        PublisherMetadata.objects(publisher_id=publisher.publisher_id).update(
            reports_project_id=project_id,
            reports_group_id=group_id,
            reports_user_id=user_id)
    else:
        noop_count += 1

close_cassandra_connection()

print('backport complete')
print('successful updates: %s' % update_count)
print('no-ops: %s' % noop_count)
