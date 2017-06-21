from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class SystemGlobal(Model):
    name = columns.Text(primary_key=True)
    int_value = columns.Integer()
    text_value = columns.Text()
    date_value = columns.DateTime()
