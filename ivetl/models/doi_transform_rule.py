from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class DoiTransformRule(Model):
    journal_code = columns.Text(primary_key=True)
    type = columns.Text(primary_key=True)
    match_expression = columns.Text(primary_key=True)
    transform_spec = columns.Text()
