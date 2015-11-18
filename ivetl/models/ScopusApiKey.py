from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Scopus_Api_Key(Model):
    key = columns.Text(primary_key=True)
