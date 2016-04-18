import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Notification_Summary(Model):
    notification_summary_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    alert_id = columns.UUID(primary_key=True)
    publisher_id = columns.Text(partition_key=True)
    product_id = columns.Text(primary_key=True)
    pipeline_id = columns.Text(primary_key=True)
    job_id = columns.Text(primary_key=True)
    message = columns.Text()
    notification_date = columns.DateTime()
    dismissed = columns.Boolean(index=True)
