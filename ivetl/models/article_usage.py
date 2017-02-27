from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class ArticleUsage(Model):
    publisher_id = columns.Text(primary_key=True)
    article_doi = columns.Text(primary_key=True)
    usage_type = columns.Text(primary_key=True)
    month_number = columns.Integer(primary_key=True)
    month_usage = columns.Integer()
    usage_start_date = columns.DateTime()
