import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class TableauNotification(Model):
    notification_id = columns.UUID(partition_key=True, default=uuid.uuid4, index=True)
    alert_id = columns.UUID(index=True)
    publisher_id = columns.Text()
    template_id = columns.Text()
    notification_date = columns.DateTime()
    expiration_date = columns.DateTime()
    name = columns.Text()
    alert_params = columns.Text()
    alert_filters = columns.Text()
    custom_message = columns.Text()
