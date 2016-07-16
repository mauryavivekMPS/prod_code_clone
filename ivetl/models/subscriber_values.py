from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class SubscriberValues(Model):
    publisher_id = columns.Text(partition_key=True)
    membership_no = columns.Text(primary_key=True)
    source = columns.Text(primary_key=True)
    name = columns.Text(primary_key=True)
    value_text = columns.Text()
