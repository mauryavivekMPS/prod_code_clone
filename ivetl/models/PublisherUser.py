from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Publisher_User(Model):
    user_email = columns.Text(primary_key=True)
    publisher_id = columns.Text()
