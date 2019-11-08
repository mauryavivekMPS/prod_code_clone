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


opts, args = getopt(sys.argv[1:], 'fp:', ['full', 'publisher'])

# single publisher vs all
pubid = None
# full refresh, delete all and reload new
full = False

fileid = 'article_citations_ds.tds' 

for opt in opts:
    if opt[0] == '-p':
        pubid = opt[1]
        logging.info('initializing single publisher run: %s' % pubid)
    elif opt[0] == '-f':
        full = True

open_cassandra_connection()

t = TableauConnector(
    username=common.TABLEAU_USERNAME,
    password=common.TABLEAU_PASSWORD,
    server=common.TABLEAU_SERVER
)

failed_workbooks = []
failed_datasources = []
failed_refreshes = []
failed_workbook_deletes = []
failed_datasource_deletes = []
failed_list_datasources = []
failed_list_workbooks = []

sw = 0
sd = 0
sr = 0
swd = 0
sdd = 0
sld = 0
slw = 0

if pubid:
    publishers = PublisherMetadata.objects.filter(publisher_id=pubid)
else:
    sys.exit()

for publisher in publishers:
    if publisher.publisher_id == 'hw':
        logging.info('skipping special-case hw publisher record')
        continue

    logging.info(
        'update_datasources_and_workbooks for: %s' % publisher.publisher_id)
    logging.info(
        'publisher.supported_product_groups = %s' %
        publisher.supported_product_groups)

    required_datasource_ids = set()
    for product_group_id in publisher.supported_product_groups:
        for datasource_id in (
            common.
            PRODUCT_GROUP_BY_ID[product_group_id]['tableau_datasources']):
            required_datasource_ids.add(datasource_id)

    logging.info('required_datasource_ids = %s' % required_datasource_ids)

    try:
        existing_datasources = t.list_datasources(
            project_id=publisher.reports_project_id)
        sld += 1
    except:
        print(f'error in list_datasources: {publisher.publisher_id}, {publisher.reports_project_id}')
        logging.info(traceback.format_exc())
        existing_datasources = []
        failed_list_datasources.append((publisher.publisher_id, publisher.reports_project_id))

    existing_datasource_ids = set([t._base_datasource_name_from_publisher_name(publisher, d['name']) for d in existing_datasources])
    datasource_tableau_id_lookup = {t._base_datasource_name_from_publisher_name(publisher, d['name']): d['id'] for d in existing_datasources}
    logging.info('existing_datasource_ids = %s' % existing_datasource_ids)

    if full:
        logging.info('full refresh; deleting all datasources')
        for datasource_id in existing_datasource_ids:
            logging.info('deleting datasource: %s' % datasource_id)
            try:
                t.delete_datasource_from_project(datasource_tableau_id_lookup[datasource_id])
                sdd += 1
            except:
                print(f'failed datasource delete: {publisher.publisher_id}, {datasource_id}')
                logging.info(traceback.format_exc())
                failed_datasource_deletes.append((publisher.publisher_id, datasource_tableau_id_lookup[datasource_id]))
            time.sleep(2)
        for datasource_id in required_datasource_ids:
            logging.info('adding datasource: %s' % datasource_id)
            try:
                t.add_datasource_to_project(publisher, datasource_id)
                sd += 1
            except:
                print(f'failed datasource add: {publisher.publisher_id}, {datasource_id}')
                logging.info(traceback.format_exc())
                failed_datasources.append((publisher.publisher_id, datasource_id))
            try:
                t.refresh_data_source(publisher, datasource_id)
                sr += 1
            except:
                print(f'failed refresh: {publisher.publisher_id}, {datasource_id}')
                logging.info(traceback.format_exc())
                failed_refreshes.append((publisher.publisher_id, datasource_id))
            time.sleep(2)
    else:
        for datasource_id in existing_datasource_ids - required_datasource_ids:
            logging.info('deleting datasource: %s' % datasource_id)
            try:
                t.delete_datasource_from_project(datasource_tableau_id_lookup[datasource_id])
                sdd += 1
            except:
                print(f'failed datasource delete: {publisher.publisher_id}, {datasource_id}')
                logging.info(traceback.format_exc())
                failed_datasource_deletes.append((publisher.publisher_id, datasource_tableau_id_lookup[datasource_id]))
            time.sleep(2)

        for datasource_id in required_datasource_ids - existing_datasource_ids:
            logging.info('adding datasource: %s' % datasource_id)
            try:
                t.add_datasource_to_project(publisher, datasource_id)
                sd += 1
            except:
                print(f'failed datasource add: {publisher.publisher_id}, {datasource_id}')
                logging.info(traceback.format_exc())
                failed_datasources.append((publisher.publisher_id, datasource_id))
                continue
            try:
                t.refresh_data_source(publisher, datasource_id)
                sr += 1
            except:
                print(f'failed refresh: {publisher.publisher_id}, {datasource_id}')
                logging.info(traceback.format_exc())
                failed_refreshes.append((publisher.publisher_id, datasource_id))
            time.sleep(2)

    required_workbook_ids = set()
    for product_group_id in publisher.supported_product_groups:
        for workbook_id in common.PRODUCT_GROUP_BY_ID[product_group_id]['tableau_workbooks']:
            required_workbook_ids.add(workbook_id)

    logging.info('required_workbook_ids = %s' % required_workbook_ids)

    try:
        existing_workbooks = t.list_workbooks(project_id=publisher.reports_project_id)
        slw += 1
    except:
        print(f'error in list_workbooks: {publisher.publisher_id}, {publisher.reports_project_id}')
        logging.info(traceback.format_exc())
        existing_workbooks = []
        failed_list_workbooks.append((publisher.publisher_id, publisher.reports_project_id))

    existing_workbook_ids = set([common.TABLEAU_WORKBOOK_ID_BY_NAME[w['name']] for w in existing_workbooks if w['name'] in common.TABLEAU_WORKBOOK_ID_BY_NAME])
    workbook_tableau_id_lookup = {common.TABLEAU_WORKBOOK_ID_BY_NAME[d['name']]: d['id'] for d in existing_workbooks if d['name'] in common.TABLEAU_WORKBOOK_ID_BY_NAME}
    logging.info('existing_workbook_ids = %s' % existing_workbook_ids)

    if full:
        logging.info('full refresh; deleting all workbooks')
        for workbook_id in existing_workbook_ids:
            logging.info('deleting workbook: %s' % workbook_id)
            try:
                t.delete_workbook_from_project(workbook_tableau_id_lookup[workbook_id])
                swd += 1
            except:
                print(f'failed workbook delete: {publisher.publisher_id}, {workbook_id}')
                logging.info(traceback.format_exc())
                failed_workbook_deletes.append((publisher.publisher_id, workbook_tableau_id_lookup[workbook_id]))
            time.sleep(2)

        for workbook_id in required_workbook_ids:
            logging.info('adding workbook: %s' % workbook_id)
            try:
                t.add_workbook_to_project(publisher, workbook_id)
                sw += 1
            except:
                print(f'failed workbook add: {publisher.publisher_id}, {workbook_id}')
                logging.info(traceback.format_exc())
                failed_workbooks.append((publisher.publisher_id, workbook_id))
            time.sleep(2)
    else:
        for workbook_id in existing_workbook_ids - required_workbook_ids:
            logging.info('deleting workbook: %s' % workbook_id)
            try:
                t.delete_workbook_from_project(workbook_tableau_id_lookup[workbook_id])
                swd += 1
            except:
                print(f'failed workbook delete: {publisher.publisher_id}, {workbook_id}')
                logging.info(traceback.format_exc())
                failed_workbook_deletes.append((publisher.publisher_id, workbook_tableau_id_lookup[workbook_id]))
            time.sleep(2)

        for workbook_id in required_workbook_ids - existing_workbook_ids:
            logging.info('adding workbook: %s' % workbook_id)
            try:
                t.add_workbook_to_project(publisher, workbook_id)
                sw += 1
            except:
                print(f'failed workbook add: {publisher.publisher_id}, {workbook_id}')
                logging.info(traceback.format_exc())
                failed_workbooks.append((publisher.publisher_id, workbook_id))
            time.sleep(2)

    time.sleep(30)

close_cassandra_connection()

print('refresh complete')
print('errors:')
print('failed workbooks:')
print(*failed_workbooks, sep=', ')
print('failed datasources:')
print(*failed_datasources, sep=', ')
print('failed refreshes:')
print(*failed_refreshes, sep=', ')
print('failed workbook deletes:')
print(*failed_workbook_deletes, sep=', ')
print('failed datasource deletes:')
print(*failed_datasource_deletes, sep=', ')
print('failed list datasources:')
print(*failed_list_datasources, sep=', ')
print('failed list workbooks:')
print(*failed_list_workbooks, sep=', ')

print('stats:')
print(f'successful workbook adds: {sw}')
print(f'successful datasource adds: {sd}')
print(f'successful refreshes: {sr}')
print(f'successful workbook deletes: {swd}')
print(f'successful datasource deletes: {sdd}')
print(f'successful list datasources: {sld}')
print(f'successful list workbooks: {slw}')

print('elapsed time:')
print(datetime.now() - start)
