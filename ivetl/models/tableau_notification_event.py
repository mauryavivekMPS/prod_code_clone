import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class TableauNotificationEvent(Model):
    notification_id = columns.UUID(partition_key=True, default=uuid.uuid4, index=True)
    event_type = columns.Text()
    event_date = columns.DateTime()
    email = columns.Text()
