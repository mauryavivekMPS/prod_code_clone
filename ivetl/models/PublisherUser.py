import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Publisher_User(Model):
    user_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    publisher_id = columns.Text(index=True)
