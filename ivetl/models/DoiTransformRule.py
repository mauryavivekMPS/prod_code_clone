from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Doi_Transform_Rule(Model):
    journal_code = columns.Text(primary_key=True)
    type = columns.Text(primary_key=True)
    match_expression = columns.Text()
    transform_spec = columns.Text()
