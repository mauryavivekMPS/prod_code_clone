from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class ContentBlock(Model):
    block_id = columns.Text(partition_key=True)
    markdown = columns.Text()
