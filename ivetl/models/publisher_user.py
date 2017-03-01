import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class PublisherUser(Model):
    user_id = columns.UUID(primary_key=True)
    publisher_id = columns.Text(primary_key=True)
    uid = columns.UUID(primary_key=True, default=uuid.uuid4)
