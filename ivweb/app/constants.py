APP_NAME = "IVWEB"

PIPELINES = [
    ('published_articles', 'Published Articles'),
    ('custom_article_data', 'Custom Article Data'),
    ('article_citations', 'Article Citations'),
    ('rejected_article_tracker', 'Rejected Articles'),
]
PIPELINE_LOOKUP = dict(PIPELINES)
