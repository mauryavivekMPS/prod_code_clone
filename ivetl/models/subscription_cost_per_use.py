from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class SubscriptionCostPerUseStat(Model):
    publisher_id = columns.Text(partition_key=True)
    membership_no = columns.Text(primary_key=True)
    bundle_name = columns.Text(primary_key=True)
    usage_date = columns.DateTime(primary_key=True)
    amount = columns.Decimal(default=0.0)
    category_usage = columns.Map(columns.Text, columns.Integer)
    total_usage = columns.Integer(default=0)
    cost_per_use = columns.Decimal(default=0.0)
