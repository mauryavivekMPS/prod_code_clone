import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Alert(Model):
    publisher_id = columns.Text(primary_key=True)
    check_id = columns.Text(primary_key=True)
    alert_id = columns.UUID(primary_key=True, default=uuid.uuid4, index=True)
    name = columns.Text()
    check_params = columns.Text()
    filter_params = columns.Text()
    emails = columns.List(columns.Text())
    enabled = columns.Boolean()
    archived = columns.Boolean(index=True)
