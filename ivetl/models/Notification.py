import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Notification(Model):
    notification_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    notification_date = columns.DateTime(index=True)
    alert_id = columns.UUID(index=True)
    publisher_id = columns.Text(index=True)
    notes = columns.Text()
    dismissed = columns.Boolean(index=True)
