from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Pipeline_Task_Status(Model):
    publisher_id = columns.Text(primary_key=True)
    pipeline_id = columns.Text(primary_key=True)
    job_id = columns.Text(primary_key=True)
    task_id = columns.Text(primary_key=True)
    duration_seconds = columns.Integer()
    end_time = columns.DateTime()
    error_details = columns.Text()
    start_time = columns.DateTime()
    status = columns.Text()
    updated = columns.DateTime()
    workfolder = columns.Text()

