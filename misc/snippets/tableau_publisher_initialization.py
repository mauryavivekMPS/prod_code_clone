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

failed_publishers = []
successful_publishers = 0

for opt in opts:
    if opt[0] == '-p':
        pubid = opt[1]
        logging.info('initializing single publisher run: %s' % pubid)

open_cassandra_connection()

# inititating user id for writing to audit log

if pubid:
    publishers = PublisherMetadata.objects.filter(publisher_id=pubid)
else:
    publishers = PublisherMetadata.objects.all()
    logging.info('running initialization for all publishers')

for publisher in publishers:
    if publisher.publisher_id == 'hw':
        logging.info('skipping special-case hw publisher record')
        continue
    publisher_id = publisher.publisher_id
    print('Starting report update for %s...' % publisher_id)

    reports_username = publisher.reports_username
    reports_password = publisher.reports_password

    PublisherMetadata.objects(publisher_id=publisher_id).update(
        reports_setup_status='in-progress',
    )

    try:
        t = TableauConnector(
            username=common.TABLEAU_USERNAME,
            password=common.TABLEAU_PASSWORD,
            server=common.TABLEAU_SERVER
        )

        print('Running initial setup')
        if publisher.demo:
            project_id, group_id, user_id = t.setup_account(publisher)
        else:
            project_id, group_id, user_id = t.setup_account(
                publisher,
                create_new_login=True,
                username=reports_username,
                password=reports_password,
            )

        PublisherMetadata.objects(publisher_id=publisher_id).update(
            reports_project_id=project_id,
            reports_group_id = group_id,
            reports_user_id = user_id,
        )

        PublisherMetadata.objects(publisher_id=publisher_id).update(
            reports_setup_status='completed',
        )

        print('Completed update')
        successful_publishers += 1

    except:
        print('Error in report update:')
        print(traceback.format_exc())
        failed_publishers.append(publisher_id)
        PublisherMetadata.objects(publisher_id=publisher_id).update(
            reports_setup_status='error',
        )

    time.sleep(2)

close_cassandra_connection()

print('initialization complete')
print('errors:')
print(*failed_publishers, sep=', ')
print('success: %s' % successful_publishers)

print('elapsed time:')
print(datetime.now() - start)
