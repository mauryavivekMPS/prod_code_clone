from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class ArticleSkipRule(Model):
    publisher_id = columns.Text(partition_key=True)
    is_cohort = columns.Boolean(primary_key=True)
    issn = columns.Text(primary_key=True)
    rule = columns.Text()
