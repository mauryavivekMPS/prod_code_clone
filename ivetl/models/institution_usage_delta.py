from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class InstitutionUsageStatDelta(Model):
    publisher_id = columns.Text(partition_key=True)
    counter_type = columns.Text(primary_key=True)
    journal = columns.Text(primary_key=True)
    subscriber_id = columns.Text(primary_key=True)
    usage_date = columns.DateTime(primary_key=True)
    usage_category = columns.Text(primary_key=True)
    time_slice = columns.Text(primary_key=True)
    previous_usage = columns.Integer()
    current_usage = columns.Integer()
    absolute_delta = columns.Integer()
    percentage_delta = columns.Float()
