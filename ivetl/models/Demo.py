import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Demo(Model):
    demo_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    publisher_name = columns.Text()
    requestor_id = columns.UUID(index=True)
    start_date = columns.DateTime()
    status = columns.Text()
    properties = columns.Text()
