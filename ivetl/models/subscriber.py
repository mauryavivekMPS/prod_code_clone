from cassandra.cqlengine import columns
from ivetl.models.base import IvetlModel


class Subscriber(IvetlModel):
    publisher_id = columns.Text(partition_key=True)
    membership_no = columns.Text(primary_key=True, index=True)
    ac_database = columns.Text()
    firstname = columns.Text()
    lastname = columns.Text()
    inst_name = columns.Text()
    user_phone = columns.Text()
    user_fax = columns.Text()
    user_email = columns.Text()
    email_domain_srch = columns.Text()
    user_address = columns.Text()
    address_2 = columns.Text()
    title = columns.Text()
    user_systemname = columns.Text()
    inst_key = columns.Text()
    modified_by_dt = columns.Text()
    subscr_type = columns.Text()
    subscr_type_desc = columns.Text()
    ringgold_id = columns.Text()
    affiliation = columns.Text()
    user_type = columns.Text(index=True)
    expired = columns.Boolean()
    num_subscriptions = columns.Integer()
    sales_agent = columns.Text()
    memo = columns.Text()
    tier = columns.Text()
    consortium = columns.Text()
    start_date = columns.DateTime()
    country = columns.Text()
    region = columns.Text()
    contact = columns.Text()
    institution_alternate_name = columns.Text()
    institution_alternate_identifier = columns.Text()
    custom1 = columns.Text()
    custom2 = columns.Text()
    custom3 = columns.Text()
    final_expiration_date = columns.DateTime()

    tableau_filter_fields = [
        'subscr_type_desc',
        'sales_agent',
        'custom1',
        'custom2',
        'custom3',
    ]
