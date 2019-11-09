from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl import hwcolumns


class PublishedArticleByCohort(Model):
    publisher_id = columns.Text(primary_key=True)
    is_cohort = columns.Boolean(primary_key=True)
    article_doi = hwcolumns.LowercaseText(primary_key=True)
    article_scopus_id = columns.Text()
    scopus_citation_count = columns.Integer()
    crossref_citation_count = columns.Integer()
    updated = columns.DateTime()
