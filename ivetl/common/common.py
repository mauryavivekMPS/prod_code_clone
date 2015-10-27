import os
import sendgrid


PIPELINES = [
    {
        'name': 'Published Articles',
        'id': 'published_articles',
        'user_facing_display_name': 'Published articles',
        'class': 'ivetl.pipelines.publishedarticles.UpdatePublishedArticlesPipeline',
        'has_file_input': False,
        'validator_class': None,
        'tasks': (
            'ivetl.pipelines.publishedarticles.tasks.GetPublishedArticlesTask',
            'ivetl.pipelines.publishedarticles.tasks.ScopusIdLookupTask',
            'ivetl.pipelines.publishedarticles.tasks.HWMetadataLookupTask',
            'ivetl.pipelines.publishedarticles.tasks.InsertPublishedArticlesIntoCassandra',
            'ivetl.pipelines.publishedarticles.tasks.ResolvePublishedArticlesData',
        )
    },
    {
        'name': 'Custom Article Data',
        'id': 'custom_article_data',
        'user_facing_display_name': 'FOAM',
        'class': 'ivetl.pipelines.customarticledata.CustomArticleDataPipeline',
        'has_file_input': True,
        'validator_class': 'ivetl.validators.CustomArticleDataValidator',
        'tasks': (
            'ivetl.pipelines.customarticledata.tasks.GetArticleDataFiles',
            'ivetl.pipelines.customarticledata.tasks.ValidateArticleDataFiles',
            'ivetl.pipelines.customarticledata.tasks.InsertCustomArticleDataIntoCassandra',
            'ivetl.pipelines.customarticledata.tasks.ResolvePublishedArticlesData',
        )
    },
    {
        'name': 'Article Citations',
        'id': 'article_citations',
        'user_facing_display_name': 'Article citations',
        'class': 'ivetl.pipelines.articlecitations.UpdateArticleCitationsPipeline',
        'has_file_input': False,
        'validator_class': None,
        'tasks': (
            'ivetl.pipelines.articlecitations.tasks.GetScopusArticleCitations',
            'ivetl.pipelines.articlecitations.tasks.InsertScopusIntoCassandra',
            'ivetl.pipelines.articlecitations.tasks.UpdateArticleCitationsWithCrossref',
        )
    },
    {
        'name': 'Rejected Articles',
        'id': 'rejected_article_tracker',
        'user_facing_display_name': 'Rejected manuscripts',
        'class': 'ivetl.rat.MonitorIncomingFileTask',
        'has_file_input': True,
        'validator_class': None,
        'tasks': ()
    },
]
PIPELINE_BY_ID = {p['id']: p for p in PIPELINES}
PIPELINE_CHOICES = [(p['id'], p['name']) for p in PIPELINES]

PRODUCTS = [
    {
        'name': 'Published Articles',
        'id': 'published_articles',
        'cohort': False,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['published_articles'],
            },
            {
                'pipeline': PIPELINE_BY_ID['custom_article_data'],
            },
            {
                'pipeline': PIPELINE_BY_ID['article_citations'],
            },
        ]
    },
    {
        'name': 'Rejected Manuscripts',
        'id': 'rejected_manuscripts',
        'cohort': False,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['rejected_article_tracker'],
            }
        ]
    },
    {
        'name': 'Cohort',
        'id': 'cohort_articles',
        'cohort': True,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['published_articles'],
            },
            {
                'pipeline': PIPELINE_BY_ID['article_citations'],
            },
        ]
    },
]
PRODUCT_BY_ID = {p['id']: p for p in PRODUCTS}
PRODUCT_CHOICES = [(p['id'], p['name']) for p in PRODUCTS]


ns = {'dc': 'http://purl.org/dc/elements/1.1/',
      'rsp': 'http://schema.highwire.org/Service/Response',
      'nlm': 'http://schema.highwire.org/NLM/Journal',
      'msg': 'http://schema.highwire.org/Service/Message',
      'c': 'http://schema.highwire.org/Compound',
      'x': 'http://www.w3.org/1999/xhtml',
      'xs': 'http://www.w3.org/2001/XMLSchema',
      'e': 'http://schema.highwire.org/Service/HPP/Expand',
      'idx': 'http://schema.highwire.org/Service/Index',
      'atom': 'http://www.w3.org/2005/Atom',
      'frz': 'http://schema.highwire.org/Service/Firenze',
      'xhtml': 'http://www.w3.org/1999/xhtml',
      'opensearch': 'http://a9.com/-/spec/opensearch/1.1',
      'hpp': 'http://schema.highwire.org/Publishing',
      'app': 'http://www.w3.org/2007/app',
      'fs': 'http://sassfs.highwire.org/Service/Content',
      'l': 'http://schema.highwire.org/Linking',
      'cache': 'http://sassfs.highwire.org/Service/Cache',
      'r': 'http://schema.highwire.org/Revision',
      'req': 'http://schema.highwire.org/Service/Request',
      'hwp': 'http://schema.highwire.org/Journal',
      'xref': 'http://www.crossref.org/qrschema/2.0',
      'results': 'http://schema.highwire.org/SQL/results'}

sass_url = "http://sass.highwire.org"

# the IVETL_ROOT env var is mandatory
if 'IVETL_ROOT' not in os.environ:
    print("You must set the IVETL_ROOT env var!")
    exit(1)

IVETL_ROOT = os.environ.get('IVETL_ROOT', '/iv')
IS_LOCAL = os.environ.get('IVETL_LOCAL', '0') == '1'
IS_QA = os.environ.get('IVETL_QA', '0') == '1'
IS_PROD = os.environ.get('IVETL_PROD', '0') == '1'

CASSANDRA_IP = os.environ.get('IVETL_CASSANDRA_IP', '127.0.0.1')
CASSANDRA_KEYSPACE_IV = os.environ.get('IVETL_CASSANDRA_KEYSPACE', 'impactvizor')

BASE_WORKING_DIR = os.environ.get('IVETL_WORKING_DIR', '/iv')
BASE_INCOMING_DIR = os.path.join(BASE_WORKING_DIR, "incoming")
BASE_WORK_DIR = os.path.join(BASE_WORKING_DIR, "working")
BASE_ARCHIVE_DIR = os.path.join(BASE_WORKING_DIR, "archive")

# these will move to the refactored pipelines soon...
RAT = RAT_DIR = "rejected_article_tracker"
AC = "article_citations"

EMAIL_TO = os.environ.get('IVETL_EMAIL_TO_ADDRESS', "nmehta@highwire.org")
EMAIL_FROM = os.environ.get('IVETL_EMAIL_FROM_ADDRESS', "impactvizor@highwire.org")
SG_USERNAME = "estacks"
SG_PWD = "Hello123!"


def send_email(subject, body):
        try:
            sg = sendgrid.SendGridClient(SG_USERNAME, SG_PWD)
            message = sendgrid.Mail()
            message.add_to(EMAIL_TO)
            message.set_subject(subject)
            message.set_html(body)
            message.set_from(EMAIL_FROM)
            sg.send(message)
        except:
            # do nothing
            print("sending of email failed")
