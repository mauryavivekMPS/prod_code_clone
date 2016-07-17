from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Subscription(Model):
    publisher_id = columns.Text(partition_key=True)
    membership_no = columns.Text(primary_key=True)
    journal_code = columns.Text(primary_key=True)
    subscr_type_cd = columns.Text(primary_key=True)
    institution_number = columns.Text()
    ac_database = columns.Text()
    expiration_dt = columns.DateTime()
    subscr_status = columns.Text()
    last_used_dt = columns.DateTime()
    modified_by_dt = columns.DateTime()
    product_cd = columns.Text()
    subscr_type = columns.Text()
    subscr_type_desc = columns.Text()
