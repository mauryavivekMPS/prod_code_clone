from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class PublishedArticleByCohort(Model):
    publisher_id = columns.Text(primary_key=True)
    is_cohort = columns.Boolean(primary_key=True)
    article_doi = columns.Text(primary_key=True)
    article_scopus_id = columns.Text()
    updated = columns.DateTime()
