from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl import hwcolumns


class ArticleCitations(Model):
    publisher_id = columns.Text(primary_key=True)
    article_doi = hwcolumns.LowercaseText(primary_key=True)
    citation_doi = hwcolumns.LowercaseText(primary_key=True)
    citation_date = columns.DateTime()
    citation_first_author = columns.Text()
    citation_issue = columns.Text()
    citation_journal_issn = columns.Text()
    citation_journal_title = columns.Text()
    citation_pages = columns.Text()
    citation_scopus_id = columns.Text()
    citation_sources = columns.List(columns.Text())
    citation_source_scopus = columns.Boolean()
    citation_source_xref = columns.Boolean()
    citation_title = columns.Text()
    citation_volume = columns.Text()
    citation_count = columns.Integer()
    created = columns.DateTime()
    updated = columns.DateTime()
    is_cohort = columns.Boolean()
