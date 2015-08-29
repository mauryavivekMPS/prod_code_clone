from cqlengine import columns
from cqlengine.models import Model


class Publisher_Vizor_Updates(Model):
    publisher_id = columns.Text(primary_key=True)
    vizor_id = columns.Text(primary_key=True)
    updated = columns.DateTime()
