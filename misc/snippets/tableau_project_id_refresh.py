import sys
import os
import time
from getopt import getopt
from datetime import datetime
import traceback
import logging

os.sys.path.append(os.environ['IVETL_ROOT'])

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    filename=os.path.join( os.environ.get('IVWEB_LOG_ROOT', '/var/log/ivweb/'), 'tableau-connector-manual.log'),
    filemode='a',
)

start = datetime.now()

from ivetl.common import common
from ivetl.models import PublisherMetadata
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.connectors import TableauConnector

# temporary logging for seeing what's happening to workbook and data source deployment


opts, args = getopt(sys.argv[1:], 'p:', ['publisher'])

# single publisher vs all
pubid = None

for opt in opts:
    if opt[0] == '-p':
        pubid = opt[1]
        logging.info('initializing single publisher run: %s' % pubid)


# open_cassandra_connection()

t = TableauConnector(
    username=common.TABLEAU_USERNAME,
    password=common.TABLEAU_PASSWORD,
    server=common.TABLEAU_SERVER
)

projects = t.list_projects()
groups = t.list_groups()
users = t.list_users()

# print(projects)
# print(groups)
# print(users)

pidx = {}
gidx = {}
uidx = {}

for project in projects:
    pidx[project['name']] = project['id']

for group in groups:
    gidx[group['name']] = group['id']

for user in users:
    uidx[user['name']] = user['id']

# print(pidx)
# print(gidx)
# print(uidx)

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
print(f'successful updates: {update_count}')
print(f'no-ops: {noop_count}')
print('elapsed time:')
print(datetime.now() - start)
