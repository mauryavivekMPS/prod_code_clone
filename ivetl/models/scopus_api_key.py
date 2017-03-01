from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class ScopusApiKey(Model):
    key = columns.Text(primary_key=True)
