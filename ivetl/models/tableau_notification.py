import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class TableauNotification(Model):
    notification_id = columns.UUID(partition_key=True, default=uuid.uuid4, index=True)
    alert_id = columns.Text(index=True)
    publisher_id = columns.Text()
    report_id = columns.Text()
    notification_date = columns.DateTime()
    name = columns.Text()
    report_params = columns.Text()
