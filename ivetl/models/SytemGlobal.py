from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl.models import Publisher_User, Publisher_Journal


class System_Global(Model):
    name = columns.Text(primary_key=True)
    int_value = columns.Integer()
    text_value = columns.Text()
    date_value = columns.DateTime()
