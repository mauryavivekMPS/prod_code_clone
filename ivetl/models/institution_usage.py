from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class InstitutionUsageStat(Model):
    publisher_id = columns.Text(partition_key=True)
    counter_type = columns.Text(partition_key=True)
    journal = columns.Text(partition_key=True)
    subscriber_id = columns.Text(primary_key=True)
    usage_date = columns.DateTime(primary_key=True, index=True)
    usage_category = columns.Text(primary_key=True)
    journal_print_issn = columns.Text()
    journal_online_issn = columns.Text()
    institution_name = columns.Text()
    usage = columns.Integer()
    bundle_name = columns.Text()
    amount = columns.Decimal()
    trial = columns.Boolean()
    trial_expiration_date = columns.DateTime()


class InstitutionUsageStatComposite(Model):
    publisher_id = columns.Text(partition_key=True)
    counter_type = columns.Text(primary_key=True)
    journal = columns.Text(primary_key=True)
    subscriber_id = columns.Text(primary_key=True)
    usage_date = columns.DateTime(primary_key=True, index=True)
    usage_category = columns.Text(primary_key=True)
    journal_print_issn = columns.Text()
    journal_online_issn = columns.Text()
    institution_name = columns.Text()
    usage = columns.Integer()
    bundle_name = columns.Text()
    amount = columns.Decimal()
    trial = columns.Boolean()
    trial_expiration_date = columns.DateTime()


class InstitutionUsageJournal(Model):
    publisher_id = columns.Text(partition_key=True)
    counter_type = columns.Text(primary_key=True)
    journal = columns.Text(primary_key=True)
