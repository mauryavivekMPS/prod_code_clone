import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class UploadedFile(Model):
    publisher_id = columns.Text(partition_key=True)
    uploaded_file_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    processed_time = columns.DateTime(primary_key=True)
    product_id = columns.Text()
    pipeline_id = columns.Text()
    job_id = columns.Text()
    path = columns.Text()
    user_id = columns.UUID()
    original_name = columns.Text()
    validated = columns.Boolean()
