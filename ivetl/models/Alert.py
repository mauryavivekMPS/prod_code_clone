import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Alert(Model):
    alert_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    publisher_id = columns.Text(primary_key=True)
    alert_type = columns.Text(index=True)
    alert_params = columns.Text()
    enabled = columns.Boolean(index=True)
