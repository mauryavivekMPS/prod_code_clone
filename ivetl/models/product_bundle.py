from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class ProductBundle(Model):
    publisher_id = columns.Text(partition_key=True)
    bundle_name = columns.Text(primary_key=True)
    journal_issns = columns.List(columns.Text())
