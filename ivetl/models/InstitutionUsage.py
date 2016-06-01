from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Institution_Usage(Model):
    institution_id = columns.Text(primary_key=True)
    month_usage = columns.Integer()
