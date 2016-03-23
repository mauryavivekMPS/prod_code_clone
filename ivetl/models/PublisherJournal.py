import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Publisher_Journal(Model):
    publisher_id = columns.Text(primary_key=True)
    product_id = columns.Text(primary_key=True)
    uid = columns.UUID(primary_key=True, default=uuid.uuid4)
    electronic_issn = columns.Text()
    print_issn = columns.Text()
    journal_code = columns.Text()
    months_until_free = columns.Integer()
