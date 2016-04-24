from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Audit_Log(Model):
    user_id = columns.UUID(primary_key=True)
    event_time = columns.DateTime(primary_key=True)
    action = columns.Text(primary_key=True)
    entity_type = columns.Text()
    entity_id = columns.Text()
