from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Publisher_Codes(Model):
    publisher_id = columns.Text(primary_key=True)
    electronic_issn = columns.Text()
    print_issn = columns.Text()
    journal_code = columns.Text()
