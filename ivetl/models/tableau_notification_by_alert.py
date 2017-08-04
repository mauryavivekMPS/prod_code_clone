from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class TableauNotificationByAlert(Model):
    publisher_id = columns.Text(partition_key=True)
    alert_id = columns.UUID(primary_key=True)
    notification_id = columns.UUID(primary_key=True)
    notification_date = columns.DateTime()
