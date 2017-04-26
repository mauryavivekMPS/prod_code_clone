from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class PublisherVizorUpdates(Model):
    publisher_id = columns.Text(primary_key=True)
    vizor_id = columns.Text(primary_key=True)
    updated = columns.DateTime()
