from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class MonthlyMessage(Model):
    product_id = columns.Text(partition_key=True)
    pipeline_id = columns.Text(partition_key=True)
    message = columns.Text()
