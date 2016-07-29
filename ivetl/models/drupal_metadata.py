from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class DrupalMetadata(Model):
    site_id = columns.Text(primary_key=True)
    site_code = columns.Text()
    name = columns.Text()
    publisher = columns.Text()
    site_url = columns.Text()
    umbrella_code = columns.Text()
    product = columns.Text()
    type = columns.Text()
    created = columns.Text()
    launch_date = columns.DateTime()
