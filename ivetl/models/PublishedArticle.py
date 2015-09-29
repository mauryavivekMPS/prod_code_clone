from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Published_Article(Model):
    publisher_id = columns.Text(primary_key=True)
    article_doi = columns.Text(primary_key=True)
    article_issue = columns.Text()
    article_journal = columns.Text()
    article_journal_issn = columns.Text()
    article_pages = columns.Text()
    article_publisher = columns.Text()
    article_scopus_id = columns.Text()
    article_title = columns.Text()
    article_volume = columns.Text()
    citations_updated_on = columns.DateTime()
    co_authors = columns.Text()
    created = columns.DateTime()
    date_of_publication = columns.DateTime()
    first_author = columns.Text()
    hw_metadata_retrieved = columns.Boolean()
    scopus_citation_count = columns.Integer()
    citations_updated_on = columns.DateTime()
    updated = columns.DateTime()
    article_type = columns.Text()
    subject_category = columns.Text()
    custom = columns.Text()
    custom_2 = columns.Text()
    custom_3 = columns.Text()
    editor = columns.Text()
    citations_lookup_error = columns.Boolean()
    is_open_access = columns.Text()
    from_rejected_manuscript = columns.Boolean()
    rejected_manuscript_id = columns.Text()
    rejected_manuscript_editor = columns.Text()
    date_of_rejection = columns.DateTime()
