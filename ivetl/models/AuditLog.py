from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Audit_Log(Model):
    user_id = columns.Text(primary_key=True)
    event_time = columns.DateTime()
    action = columns.Text()
    entity_type = columns.Text()
    entity_id = columns.Text()
