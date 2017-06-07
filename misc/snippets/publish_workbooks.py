from ivetl.models import PublisherMetadata
from ivetl.connectors import TableauConnector
from ivetl.common import common

publisher = PublisherMetadata.objects.get(publisher_id='blood')
t = TableauConnector(
    username=common.TABLEAU_USERNAME,
    password=common.TABLEAU_PASSWORD,
    server=common.TABLEAU_SERVER
)
t.update_datasources_and_workbooks(publisher)
