from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class UptimeCheckMetadata(Model):
    publisher_id = columns.Text(primary_key=True)
    check_id = columns.Integer(primary_key=True)
    check_type = columns.Text()
    check_name = columns.Text()
    check_url = columns.Text()
    pingdom_account = columns.Text()
    site_code = columns.Text()
    site_name = columns.Text()
    site_type = columns.Text()
    site_platform = columns.Text()
    publisher_name = columns.Text()
    publisher_code = columns.Text()
    drupal_launch_date = columns.DateTime()
