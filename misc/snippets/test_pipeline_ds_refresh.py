import sys
import os
from getopt import getopt
import traceback
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    filename=os.path.join( os.environ.get('IVWEB_LOG_ROOT', '/var/log/ivweb/'), 'tableau-connector-manual.log'),
    filemode='a',
)

os.sys.path.append(os.environ['IVETL_ROOT'])

from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.common import common
from ivetl.connectors import TableauConnector
from ivetl.models import PublisherMetadata

opts, args = getopt(sys.argv[1:], 'hfl:p:o:e:', [
    'help',
    'publisher'])

publisher_id = None
email = None
product_id = 'article_citations'
pipeline_id = 'article_citations'
helptext = '''usage: python test_pipeline_ds_refresh.py -- [ -h -e email ] -p publisher_id

Environment variables:

This script uses the open_cassandra_connection and close_cassandra_connection
routines defined in celery.py, which in turn use variables defined in common.py.
The Cassandra IP list can be set with the following variable, e.g:

export IVETL_CASSANDRA_IP=bk-vizor-dev-01.highwire.org

Use a comma separated list for multiple hosts.

Options and arguments:
-h     :  print this help message and exit (also --help)
-e     :  email address to test/send developer notification email for failures
-p     :  publisher_id value to use when querying cassandra. required.
'''

for opt in opts:
    if opt[0] == '-h':
        print(helptext)
        sys.exit()
    if opt[0] == '-e':
        email = opt[1]
    if opt[0] == '-p':
        publisher_id = opt[1]
        print('initializing single publisher run: %s' % publisher_id)

if not publisher_id:
    print('-p: publisher id required')
    sys.exit()

# ivetl/pipelines/base_task.py lines 188-225 modified slightly for testing

open_cassandra_connection()

publishers = [PublisherMetadata.objects.get(publisher_id=publisher_id)]

for publisher in publishers:

    # update the data in tableau
    t = TableauConnector(
        username=common.TABLEAU_USERNAME,
        password=common.TABLEAU_PASSWORD,
        server=common.TABLEAU_SERVER
    )

    all_modified_datasources = set(common.TABLEAU_DATASOURCE_UPDATES.get((product_id, pipeline_id), []))
    #removed lines
    all_datasources_to_update = all_modified_datasources
    print(all_datasources_to_update)
    pub_ds_to_update = set([
        t._publisher_datasource_name(publisher, ds) for
        ds in all_datasources_to_update
    ])
    print(pub_ds_to_update)
    tableau_ds_to_update = t.list_datasources_by_names(
        pub_ds_to_update, publisher)
    print(tableau_ds_to_update)
    ds_ids_to_update = [d['id'] for d in tableau_ds_to_update]
    print(ds_ids_to_update)
    if email:
        ds_ids_to_update.append('a-fake-id-that-will-cause-failure')
    for datasource_id in ds_ids_to_update:
        loginfo = (publisher.publisher_id, datasource_id)
        print('Refreshing datasource: %s -> %s' % loginfo)
        try:
            t.refresh_data_source(datasource_id)
        except:
            print('Refresh failed for %s, -> %s' % loginfo)
            subject = 'Impact Vizor (%s): Refresh Failed: %s, %s' % (
                publisher_id, product_id, pipeline_id
            )
            body = ('<p>Refresh failed for publisher, tableau_datasource_id: '
                '%s, %s</p>' % (
                    publisher.publisher_id,
                    datasource_id
                ))

            body += ('<p>Pipeline: (product_id, pipeline_id): '
                '%s, %s.</p>' % (product_id, pipeline_id))


            body += ('<p>Tableau REST API Docs:</p>'
            '<p>https://help.tableau.com'
                '/v2019.4/api/rest_api/en-us/REST/'
                'rest_api_ref_datasources.htm'
                '#update_data_source_now</p>'
            '<p>POST /api/api-version/sites/$site-id'
            '/datasources/$datasource-id/refresh</p>')

            body += ('The action that failed is equivalent to'
                ' selecting a data source using the '
                'Tableau Server UI, and then '
                'selecting Refresh Extracts from '
                'the menu (also known as a "manual refresh").')

            body += ('<p>An operator, developer, or support staff'
                ' member should check the current status of '
                'Tableau Server, diagnose the failure reason,'
                ' and attempt to re-run the refresh manually.</p>')

            body += '<p>Thank you,<br/>Impact Vizor Team</p>'

            common.send_email(subject, body, to=email)
            continue

close_cassandra_connection()
