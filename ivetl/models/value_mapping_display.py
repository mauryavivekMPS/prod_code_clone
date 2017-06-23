from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class ValueMappingDisplay(Model):
    publisher_id = columns.Text(partition_key=True)
    mapping_type = columns.Text(primary_key=True)
    canonical_value = columns.Text(primary_key=True)
    display_value = columns.Text()
