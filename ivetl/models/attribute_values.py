from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class AttributeValues(Model):
    publisher_id = columns.Text(partition_key=True)
    name = columns.Text(primary_key=True)
    values_json = columns.Text()
