from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Published_Article_Values(Model):

    publisher_id = columns.Text(primary_key=True)
    article_doi = columns.Text(primary_key=True)
    source = columns.Text(index=True)
    name = columns.Text(index=True)
    value = columns.Text()