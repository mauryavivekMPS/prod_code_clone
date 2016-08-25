from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class PipelineTaskStatus(Model):
    publisher_id = columns.Text(primary_key=True)
    product_id = columns.Text(primary_key=True)
    pipeline_id = columns.Text(primary_key=True)
    job_id = columns.Text(primary_key=True)
    task_id = columns.Text(primary_key=True)
    duration_seconds = columns.Integer()
    current_record_count = columns.Integer()
    total_record_count = columns.Integer()
    end_time = columns.DateTime()
    error_details = columns.Text()
    start_time = columns.DateTime()
    status = columns.Text()
    updated = columns.DateTime()
    workfolder = columns.Text()
    task_args_json = columns.Text()

    def percent_complete(self):
        if self.total_record_count:
            return int(self.current_record_count / self.total_record_count * 100)
        else:
            return 0
