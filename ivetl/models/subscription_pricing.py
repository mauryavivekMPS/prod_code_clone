from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class SubscriptionPricing(Model):
    publisher_id = columns.Text(partition_key=True)
    membership_no = columns.Text(primary_key=True)
    year = columns.Integer(primary_key=True)
    bundle_name = columns.Text(primary_key=True)
    trial = columns.Boolean()
    trial_expiration_date = columns.DateTime()
    amount = columns.Decimal()
