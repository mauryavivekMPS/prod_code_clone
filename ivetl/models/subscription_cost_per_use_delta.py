from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class SubscriptionCostPerUseStatDelta(Model):
    publisher_id = columns.Text(partition_key=True)
    membership_no = columns.Text(primary_key=True)
    bundle_name = columns.Text(primary_key=True)
    time_slice = columns.Text(primary_key=True)
    usage_date = columns.DateTime(primary_key=True)
    previous_cost_per_use = columns.Float()
    current_cost_per_use = columns.Float()
    absolute_delta = columns.Integer()
    percentage_delta = columns.Float()
