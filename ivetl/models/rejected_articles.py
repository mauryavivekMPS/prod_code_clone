from cassandra.cqlengine import columns
from ivetl.models.base import IvetlModel
from ivetl import hwcolumns


class RejectedArticles(IvetlModel):
    publisher_id = columns.Text(primary_key=True)
    rejected_article_id = columns.TimeUUID(primary_key=True)
    article_type = columns.Text(required=False)
    authors_match_score = columns.Decimal(required=False)
    citation_lookup_status = columns.Text(required=False)
    citations = columns.Integer(required=False)
    co_authors = columns.Text(required=False)
    corresponding_author = columns.Text(required=False)
    created = columns.DateTime()
    crossref_doi = hwcolumns.LowercaseText(required=False)
    crossref_match_score = columns.Decimal(required=False)
    custom = columns.Text(required=False)
    custom_2 = columns.Text(required=False)
    custom_3 = columns.Text(required=False)
    date_of_publication = columns.DateTime(required=False)
    date_of_rejection = columns.DateTime()
    editor = columns.Text()
    first_author = columns.Text(required=False)
    keywords = columns.Text(required=False)
    manuscript_id = columns.Text(index=True)
    manuscript_title = columns.Text()
    published_co_authors = columns.Text(required=False)
    published_first_author = columns.Text(required=False)
    published_journal = columns.Text(required=False)
    published_journal_issn = columns.Text(required=False)
    published_publisher = columns.Text(required=False)
    published_title = columns.Text(required=False)
    reject_reason = columns.Text()
    scopus_doi_status = columns.Text(required=False)
    scopus_id = columns.Text(required=False)
    source_file_name = columns.Text()
    status = columns.Text()
    subject_category = columns.Text(required=False)
    submitted_journal = columns.Text(index=True)
    mendeley_saves = columns.Integer(required=False)
    preprint_doi = hwcolumns.LowercaseText(required=False)
    updated = columns.DateTime()

    tableau_filter_fields = [
        'submitted_journal',
        'reject_reason',
        'subject_category',
        'article_type',
        'editor',
        'custom',
        'custom_2',
        'custom_3',
        'published_publisher',
        'published_journal',
    ]
