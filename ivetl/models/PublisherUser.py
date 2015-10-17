from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Publisher_User(Model):
    user_id = columns.Text(primary_key=True)
    publisher_id = columns.Text()
