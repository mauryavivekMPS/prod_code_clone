from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Uptime_Check(Model):
    publisher_id = columns.Text(primary_key=True)
    check_id = columns.Integer(primary_key=True)
    check_type = columns.Text()
    check_date = columns.DateTime()
    check_name = columns.Text()
    check_url = columns.Text()
    pingdom_account = columns.Text()
    site_code = columns.Text()
    site_name = columns.Text()
    site_type = columns.Text()
    site_platform = columns.Text()
    publisher_name = columns.Text()
    publisher_code = columns.Text()
    avg_response_ms = columns.Integer()
    total_up_sec = columns.Integer()
    total_down_sec = columns.Integer()
    total_unknown_sec = columns.Integer()
