from cqlengine import columns
from cqlengine.models import Model


class Issn_Journal(Model):
    issn = columns.Text(primary_key=True)
    journal = columns.Text()
    publisher = columns.Text()