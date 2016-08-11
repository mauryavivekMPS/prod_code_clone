from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class SubscriptionCostPerUseByBundleStatDelta(Model):
    publisher_id = columns.Text(partition_key=True)
    membership_no = columns.Text(primary_key=True)
    bundle_name = columns.Text(primary_key=True)
    usage_date = columns.DateTime(primary_key=True)
    time_slice = columns.Text(primary_key=True)
    previous_cost_per_use = columns.Decimal()
    current_cost_per_use = columns.Decimal()
    absolute_delta = columns.Decimal()
    percentage_delta = columns.Float()

    __table_name__ = 'subscription_cpu_by_bundle_stat_delta'


class SubscriptionCostPerUseBySubscriberStatDelta(Model):
    publisher_id = columns.Text(partition_key=True)
    membership_no = columns.Text(primary_key=True)
    usage_date = columns.DateTime(primary_key=True)
    time_slice = columns.Text(primary_key=True)
    previous_cost_per_use = columns.Decimal()
    current_cost_per_use = columns.Decimal()
    absolute_delta = columns.Decimal()
    percentage_delta = columns.Float()

    __table_name__ = 'subscription_cpu_by_subscriber_stat_delta'
