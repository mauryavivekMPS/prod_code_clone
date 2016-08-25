from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class ServiceResponseCode(Model):
    publisher_id = columns.Text(partition_key=True)
    name = columns.Text(primary_key=True)
    from_date = columns.DateTime(primary_key=True)
    until_date = columns.DateTime(primary_key=True)
    status_code = columns.Text(primary_key=True)
    sample = columns.Integer()
    count = columns.Integer()
