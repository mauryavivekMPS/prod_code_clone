from ivetl.pipelines.publishedarticles.tasks.get_published_articles import GetPublishedArticlesTask
from ivetl.pipelines.publishedarticles.tasks.get_highwire_metadata import GetHighWireMetadataTask
from ivetl.pipelines.publishedarticles.tasks.mendeley_lookup_task import MendeleyLookupTask
from ivetl.pipelines.publishedarticles.tasks.insert_published_articles_into_cassandra import InsertPublishedArticlesIntoCassandra
from ivetl.pipelines.publishedarticles.tasks.scopus_id_lookup import ScopusIdLookupTask
from ivetl.pipelines.publishedarticles.tasks.resolve_published_articles_data import ResolvePublishedArticlesData
from ivetl.pipelines.publishedarticles.tasks.resolve_article_usage_data import ResolveArticleUsageData
from ivetl.pipelines.publishedarticles.tasks.check_rejected_manuscript import CheckRejectedManuscriptTask
from ivetl.pipelines.publishedarticles.tasks.insert_placeholder_citations_into_cassandra import InsertPlaceholderCitationsIntoCassandraTask
from ivetl.pipelines.publishedarticles.tasks.update_attribute_values_cache import UpdateAttributeValuesCacheTask
from ivetl.pipelines.publishedarticles.tasks.get_social_metrics import GetSocialMetricsTask