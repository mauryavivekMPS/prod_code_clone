from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Institution_Metadata(Model):
    institution_id = columns.Text(primary_key=True)
    institution_code = columns.Text()
    name = columns.Text()
    created = columns.Text()
