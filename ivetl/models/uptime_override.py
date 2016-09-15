import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class UptimeOverride(Model):
    override_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    start_date = columns.DateTime()
    end_date = columns.DateTime()
    match_type = columns.Text()
    match_value = columns.Text()
    override_type = columns.Text()
