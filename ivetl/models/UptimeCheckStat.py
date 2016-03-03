from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Uptime_Check_Stat(Model):
    publisher_id = columns.Text(primary_key=True)
    check_id = columns.Integer(primary_key=True)
    check_date = columns.DateTime(primary_key=True)
    avg_response_ms = columns.Integer()
    total_up_sec = columns.Integer()
    total_down_sec = columns.Integer()
    total_unknown_sec = columns.Integer()
