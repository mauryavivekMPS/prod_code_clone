from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Issn_Journal(Model):

    issn = columns.Text(primary_key=True)
    journal = columns.Text()
    publisher = columns.Text()