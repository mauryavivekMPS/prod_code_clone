from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Publisher_User(Model):
    publisher_id = columns.Text(primary_key=True)
    user_email = columns.Text(primary_key=True)
