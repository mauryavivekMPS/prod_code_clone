from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class SubscriptionCostPerUse(Model):
    publisher_id = columns.Text(partition_key=True)
    membership_no = columns.Text(primary_key=True)
    bundle_name = columns.Text(primary_key=True)
    month = columns.Integer(primary_key=True)
    amount = columns.Decimal()
    usage = columns.Integer()
    cost_per_use = columns.Decimal()
