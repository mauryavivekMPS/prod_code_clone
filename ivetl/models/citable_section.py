from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class CitableSection(Model):
    publisher_id = columns.Text(partition_key=True)
    journal_issn = columns.Text(primary_key=True)
    article_type = columns.Text(primary_key=True)
