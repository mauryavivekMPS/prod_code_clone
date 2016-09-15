from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class SingletonTaskStatus(Model):
    task_type = columns.Text(partition_key=True)
    task_id = columns.Text(primary_key=True)
    status = columns.Text()
    start_time = columns.DateTime()
    end_time = columns.DateTime()
    properties_json = columns.Text(default="{}")
