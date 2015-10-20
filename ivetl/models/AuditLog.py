import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Audit_Log(Model):
    user_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    event_time = columns.DateTime()
    action = columns.Text()
    entity_type = columns.Text()
    entity_id = columns.Text()
