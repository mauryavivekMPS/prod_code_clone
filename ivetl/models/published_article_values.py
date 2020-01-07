from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl import hwcolumns


class PublishedArticleValues(Model):
    publisher_id = columns.Text(primary_key=True)
    article_doi = hwcolumns.LowercaseText(primary_key=True)
    source = columns.Text(primary_key=True)
    name = columns.Text(primary_key=True)
    value_text = columns.Text()
