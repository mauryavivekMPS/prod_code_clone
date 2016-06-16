from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class PublishedArticle(Model):
    publisher_id = columns.Text(primary_key=True)
    article_doi = columns.Text(primary_key=True)
    article_issue = columns.Text()
    article_journal = columns.Text()
    article_journal_issn = columns.Text()
    article_pages = columns.Text()
    article_publisher = columns.Text()
    article_scopus_id = columns.Text()
    article_title = columns.Text()
    article_type = columns.Text()
    article_volume = columns.Text()
    citations_lookup_error = columns.Boolean()
    citations_updated_on = columns.DateTime()
    co_authors = columns.Text()
    created = columns.DateTime()
    custom = columns.Text()
    custom_2 = columns.Text()
    custom_3 = columns.Text()
    date_of_publication = columns.DateTime()
    date_of_rejection = columns.DateTime()
    editor = columns.Text()
    first_author = columns.Text()
    from_rejected_manuscript = columns.Boolean()
    has_abstract = columns.Boolean()
    hw_metadata_retrieved = columns.Boolean()
    is_cohort = columns.Boolean()
    is_open_access = columns.Text()
    rejected_manuscript_editor = columns.Text()
    rejected_manuscript_id = columns.Text()
    scopus_citation_count = columns.Integer()
    subject_category = columns.Text()
    month_usage_03 = columns.Integer()
    month_usage_06 = columns.Integer()
    month_usage_09 = columns.Integer()
    month_usage_12 = columns.Integer()
    month_usage_24 = columns.Integer()
    month_usage_36 = columns.Integer()
    month_usage_48 = columns.Integer()
    month_usage_60 = columns.Integer()
    month_usage_full_03 = columns.Integer()
    month_usage_full_06 = columns.Integer()
    month_usage_full_09 = columns.Integer()
    month_usage_full_12 = columns.Integer()
    month_usage_full_24 = columns.Integer()
    month_usage_full_36 = columns.Integer()
    month_usage_full_48 = columns.Integer()
    month_usage_full_60 = columns.Integer()
    month_usage_pdf_03 = columns.Integer()
    month_usage_pdf_06 = columns.Integer()
    month_usage_pdf_09 = columns.Integer()
    month_usage_pdf_12 = columns.Integer()
    month_usage_pdf_24 = columns.Integer()
    month_usage_pdf_36 = columns.Integer()
    month_usage_pdf_48 = columns.Integer()
    month_usage_pdf_60 = columns.Integer()
    month_usage_abstract_03 = columns.Integer()
    month_usage_abstract_06 = columns.Integer()
    month_usage_abstract_09 = columns.Integer()
    month_usage_abstract_12 = columns.Integer()
    month_usage_abstract_24 = columns.Integer()
    month_usage_abstract_36 = columns.Integer()
    month_usage_abstract_48 = columns.Integer()
    month_usage_abstract_60 = columns.Integer()
    usage_start_date = columns.DateTime()
    mendeley_saves = columns.Integer()
    altmetrics_facebook = columns.Integer()
    altmetrics_blogs = columns.Integer()
    altmetrics_twitter = columns.Integer()
    altmetrics_gplus = columns.Integer()
    altmetrics_news_outlets = columns.Integer()
    altmetrics_wikipedia = columns.Integer()
    altmetrics_video = columns.Integer()
    altmetrics_policy_docs = columns.Integer()
    altmetrics_reddit = columns.Integer()
    f1000_total_score = columns.Integer()
    f1000_num_recommendations = columns.Integer()
    f1000_average_score = columns.Decimal()
    citation_count = columns.Integer()
    updated = columns.DateTime()
