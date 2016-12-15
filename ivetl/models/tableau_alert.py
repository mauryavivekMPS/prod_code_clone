import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class TableauAlert(Model):
    alert_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    publisher_id = columns.Text(partition_key=True)
    name = columns.Text()
    report_id = columns.Text(primary_key=True)
    alert_params = columns.Text()
    alert_filters = columns.Text()
    emails = columns.List(columns.Text())
    enabled = columns.Boolean()
    archived = columns.Boolean(index=True)
