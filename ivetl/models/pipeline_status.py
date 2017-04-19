from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class PipelineStatus(Model):
    publisher_id = columns.Text(partition_key=True)
    product_id = columns.Text(primary_key=True)
    pipeline_id = columns.Text(primary_key=True)
    job_id = columns.Text(primary_key=True)
    current_task = columns.Text()
    current_task_count = columns.Integer()
    total_task_count = columns.Integer()
    duration_seconds = columns.Integer()
    end_time = columns.DateTime()
    error_details = columns.Text()
    start_time = columns.DateTime()
    status = columns.Text()
    updated = columns.DateTime()
    workfolder = columns.Text()
    user_email = columns.Text()
    params_json = columns.Text()
    stop_instruction = columns.Text()

    def display_name(self):
        return self.job_id[self.job_id.rindex('_') + 1:]

    def percent_complete(self):
        if self.total_task_count and self.current_task_count:
            # btw, decrement task count because the task isn't done until we're at the next one
            return int((self.current_task_count - 1) / self.total_task_count * 100)
        else:
            return 0
