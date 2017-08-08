from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class AuditLogByUser(Model):
    user_id = columns.UUID(partition_key=True)
    event_time = columns.DateTime(primary_key=True)
    action = columns.Text(primary_key=True)
    publisher_id = columns.Text()
    description = columns.Text()


class AuditLogByPublisher(Model):
    publisher_id = columns.Text(partition_key=True)
    event_time = columns.DateTime(primary_key=True)
    action = columns.Text(primary_key=True)
    user_id = columns.UUID()
    description = columns.Text()


class AuditLogByTime(Model):
    month = columns.Text(partition_key=True)
    event_time = columns.DateTime(primary_key=True)
    action = columns.Text(primary_key=True)
    publisher_id = columns.Text()
    user_id = columns.UUID()
    description = columns.Text()
