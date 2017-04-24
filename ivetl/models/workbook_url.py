from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class WorkbookUrl(Model):
    publisher_id = columns.Text(partition_key=True)
    workbook_id = columns.Text(primary_key=True)
    url = columns.Text()
