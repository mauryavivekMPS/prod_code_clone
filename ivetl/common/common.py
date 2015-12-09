import os
import importlib
import sendgrid


PIPELINES = [
    {
        'name': 'Published Articles',
        'id': 'published_articles',
        'user_facing_display_name': 'Published articles',
        'class': 'ivetl.pipelines.publishedarticles.UpdatePublishedArticlesPipeline',
        'has_file_input': False,
        'validator_class': None,
        'tableau_data_source_id': None,
    },
    {
        'name': 'Custom Article Data',
        'id': 'custom_article_data',
        'user_facing_display_name': 'Additional metadata files',
        'class': 'ivetl.pipelines.customarticledata.CustomArticleDataPipeline',
        'has_file_input': True,
        'validator_class': 'ivetl.validators.CustomArticleDataValidator',
        'format_file': 'AdditionalMetadata-Format.pdf',
        'tableau_data_source_id': 'article_citations',
    },
    {
        'name': 'Article Citations',
        'id': 'article_citations',
        'user_facing_display_name': 'Article citations',
        'class': 'ivetl.pipelines.articlecitations.UpdateArticleCitationsPipeline',
        'has_file_input': False,
        'validator_class': None,
        'tableau_data_source_id': 'article_citations',
    },
    {
        'name': 'Rejected Articles',
        'id': 'rejected_articles',
        'user_facing_display_name': 'Rejected manuscripts',
        'class': 'ivetl.pipelines.rejectedarticles.UpdateRejectedArticlesPipeline',
        'has_file_input': True,
        'validator_class': 'ivetl.validators.RejectedArticlesValidator',
        'format_file': 'RejectedArticles-Format.pdf',
        'tableau_data_source_id': 'rejected_articles',
    },
    {
        'name': 'Check Rejected Manuscripts',
        'id': 'check_rejected_manuscripts',
        'class': 'ivetl.pipelines.publishedarticles.CheckRejectedManuscriptsPipeline',
        'has_file_input': False,
        'validator_class': None,
        'tableau_data_source_id': None,
    },
    {
        'name': 'Insert Placeholder Citations',
        'id': 'insert_placeholder_citations',
        'class': 'ivetl.pipelines.publishedarticles.InsertPlaceholderCitationsPipeline',
        'has_file_input': False,
        'validator_class': None,
        'tableau_data_source_id': None,
    },
    {
        'name': 'Update Manuscripts',
        'id': 'update_manuscripts',
        'class': 'ivetl.pipelines.rejectedarticles.UpdateManuscriptsPipeline',
        'has_file_input': False,
        'validator_class': None,
        'tableau_data_source_id': None,
    },
    {
        'name': 'XREF Journal Catalog',
        'id': 'xref_journal_catalog',
        'class': 'ivetl.pipelines.rejectedarticles.XREFJournalCatalogPipeline',
        'has_file_input': False,
        'validator_class': None,
        'tableau_data_source_id': None,
    },
]
PIPELINE_BY_ID = {p['id']: p for p in PIPELINES}
PIPELINE_CHOICES = [(p['id'], p['name']) for p in PIPELINES]


def get_pipeline_class(pipeline):
    pipeline_module_name, class_name = pipeline['class'].rsplit('.', 1)
    return getattr(importlib.import_module(pipeline_module_name), class_name)


def get_validator_class(pipeline):
    validator_module_name, class_name = pipeline['validator_class'].rsplit('.', 1)
    return getattr(importlib.import_module(validator_module_name), class_name)


PRODUCTS = [
    {
        'name': 'Published Articles',
        'id': 'published_articles',
        'icon': 'lnr-layers',
        'is_user_facing': True,
        'order': 1,
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
        ],
        'tableau_workbooks': [
            'section_performance_analyzer_workbook',
            'hot_article_tracker_workbook',
            'hot_object_tracker_workbook',
            'citation_distribution_surveyor_workbook',
        ]
    },
    {
        'name': 'Rejected Manuscripts',
        'id': 'rejected_manuscripts',
        'icon': 'lnr-layers-crossed',
        'is_user_facing': True,
        'order': 2,
        'cohort': False,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['rejected_articles'],
            }
        ],
        'tableau_workbooks': [
            'rejected_article_tracker_workbook',
        ]
    },
    {
        'name': 'Cohort Articles',
        'id': 'cohort_articles',
        'icon': 'lnr-icons2',
        'is_user_facing': True,
        'order': 3,
        'cohort': True,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['published_articles'],
            },
            {
                'pipeline': PIPELINE_BY_ID['article_citations'],
            },
        ],
        'tableau_workbooks': [
            'cohort_comparator_workbook',
        ]
    },
    {
        'name': 'Check Rejected Manuscripts',
        'id': 'check_rejected_manuscripts',
        'is_user_facing': False,
        'order': 4,
        'cohort': False,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['check_rejected_manuscripts'],
            }
        ],
        'tableau_workbooks': [],
    },
    {
        'name': 'Insert Placeholder Citations',
        'id': 'insert_placeholder_citations',
        'is_user_facing': False,
        'order': 5,
        'cohort': False,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['insert_placeholder_citations'],
            }
        ],
        'tableau_workbooks': [],
    },
    {
        'name': 'Update Manuscripts',
        'id': 'update_manuscripts',
        'is_user_facing': False,
        'order': 6,
        'cohort': False,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['update_manuscripts'],
            }
        ],
        'tableau_workbooks': [],
    },
    {
        'name': 'XREF Journal Catalog',
        'id': 'xref_journal_catalog',
        'is_user_facing': False,
        'order': 7,
        'cohort': False,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['xref_journal_catalog'],
            }
        ],
        'tableau_workbooks': [],
    },
]
PRODUCT_BY_ID = {p['id']: p for p in PRODUCTS}
PRODUCT_CHOICES = [(p['id'], p['name']) for p in PRODUCTS]

FTP_DIRS = [
    {
        'product_id': 'published_articles',
        'pipeline_id': 'custom_article_data',
        'ftp_dir_name': 'additional_metadata_files',
    },
    {
        'product_id': 'rejected_manuscripts',
        'pipeline_id': 'rejected_articles',
        'ftp_dir_name': 'rejected_manuscripts',
    },
]
PRODUCT_ID_BY_FTP_DIR_NAME = {f['ftp_dir_name']: f['product_id'] for f in FTP_DIRS}
PIPELINE_ID_BY_FTP_DIR_NAME = {f['ftp_dir_name']: f['pipeline_id'] for f in FTP_DIRS}


def get_ftp_dir_name(product_id, pipeline_id):
    for d in FTP_DIRS:
        if d['product_id'] == product_id and d['pipeline_id'] == pipeline_id:
            return d['ftp_dir_name']
    return None


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
BASE_FTP_DIR = os.path.join(BASE_WORKING_DIR, "ftp")
BASE_WORK_DIR = os.path.join(BASE_WORKING_DIR, "working")
BASE_ARCHIVE_DIR = os.path.join(BASE_WORKING_DIR, "archive")

TABLEAU_SERVER = os.environ.get('TABLEAU_SERVER', 'http://10.0.0.143')
TABLEAU_USERNAME = os.environ.get('TABLEAU_USERNAME', 'admin')
TABLEAU_PASSWORD = os.environ.get('TABLEAU_PASSWORD', 'admin')

EMAIL_TO = os.environ.get('IVETL_EMAIL_TO_ADDRESS', "nmehta@highwire.org")
EMAIL_FROM = os.environ.get('IVETL_EMAIL_FROM_ADDRESS', "impactvizor@highwire.org")
SG_USERNAME = "estacks"
SG_PWD = "Hello123!"


def send_email(subject, body, to=EMAIL_TO, format="html"):
    try:
        sg = sendgrid.SendGridClient(SG_USERNAME, SG_PWD)
        message = sendgrid.Mail()
        message.add_to(to)
        message.set_subject(subject)
        if format == 'html':
            message.set_html(body)
        elif format == 'test':
            message.set_text(body)
        message.set_from(EMAIL_FROM)
        sg.send(message)
    except:
        # do nothing
        print("sending of email failed")
