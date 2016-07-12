from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class SubscriberValues(Model):
    # TODO: update this
    publisher_id = columns.Text(primary_key=True)
    article_doi = columns.Text(primary_key=True)
    source = columns.Text(primary_key=True)
    name = columns.Text(primary_key=True)
    value_text = columns.Text()
