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
        'rebuild_data_source_id': ['article_citations', 'article_usage'],
    },
    {
        'name': 'Custom Article Data',
        'id': 'custom_article_data',
        'user_facing_display_name': 'Additional metadata',
        'class': 'ivetl.pipelines.customarticledata.CustomArticleDataPipeline',
        'has_file_input': True,
        'validator_class': 'ivetl.validators.CustomArticleDataValidator',
        'format_file': 'AdditionalMetadata-Format.pdf',
        'rebuild_data_source_id': ['article_citations'],
    },
    {
        'name': 'Article Citations',
        'id': 'article_citations',
        'user_facing_display_name': 'Article citations',
        'class': 'ivetl.pipelines.articlecitations.UpdateArticleCitationsPipeline',
        'has_file_input': False,
        'validator_class': None,
        'rebuild_data_source_id': ['article_citations'],
    },
    {
        'name': 'Article Usage',
        'id': 'article_usage',
        'user_facing_display_name': 'Article usage',
        'class': 'ivetl.pipelines.articleusage.ArticleUsagePipeline',
        'has_file_input': True,
        'validator_class': 'ivetl.validators.ArticleUsageValidator',
        'rebuild_data_source_id': ['article_citations', 'article_usage'],
    },
    {
        'name': 'Social Metrics',
        'id': 'social_metrics',
        'user_facing_display_name': 'Social metrics',
        'class': 'ivetl.pipelines.socialmetrics.SocialMetricsPipeline',
        'has_file_input': False,
        'validator_class': None,
        'rebuild_data_source_id': None,
        'hide_demo_filter': True,
        'single_publisher_pipeline': True,
        'single_publisher_id': 'hw',
        'pipeline_run_button_label': 'Get Latest Social Metrics',
    },
    {
        'name': 'Upload Rejected',
        'id': 'rejected_articles',
        'user_facing_display_name': 'Rejected manuscripts',
        'class': 'ivetl.pipelines.rejectedarticles.UpdateRejectedArticlesPipeline',
        'has_file_input': True,
        'validator_class': 'ivetl.validators.RejectedArticlesValidator',
        'format_file': 'RejectedArticles-Format.pdf',
        'rebuild_data_source_id': ['rejected_articles'],
    },
    {
        'name': 'Bench Press Rejected',
        'id': 'benchpress_rejected_articles',
        'user_facing_display_name': 'Rejected manuscripts',
        'class': 'ivetl.pipelines.rejectedarticles.GetRejectedArticlesFromBenchPressPipeline',
        'has_file_input': False,
        'rebuild_data_source_id': ['rejected_articles'],
        'include_date_range_controls': True,
        'filter_for_benchpress_support': True,
        'supports_restart': True,
    },
    {
        'name': 'Reprocess Rejected',
        'id': 'reprocess_rejected_articles',
        'user_facing_display_name': 'Reprocess rejected manuscripts',
        'class': 'ivetl.pipelines.rejectedarticles.ReprocessRejectedArticlesPipeline',
        'has_file_input': False,
        'validator_class': None,
        'rebuild_data_source_id': ['rejected_articles'],
    },
    {
        'name': 'Check Rejected Manuscripts',
        'id': 'check_rejected_manuscripts',
        'class': 'ivetl.pipelines.publishedarticles.CheckRejectedManuscriptsPipeline',
        'has_file_input': False,
        'validator_class': None,
        'rebuild_data_source_id': None,
    },
    {
        'name': 'Insert Placeholder Citations',
        'id': 'insert_placeholder_citations',
        'class': 'ivetl.pipelines.publishedarticles.InsertPlaceholderCitationsPipeline',
        'has_file_input': False,
        'validator_class': None,
        'rebuild_data_source_id': None,
    },
    {
        'name': 'Update Manuscripts',
        'id': 'update_manuscripts',
        'class': 'ivetl.pipelines.rejectedarticles.UpdateManuscriptsPipeline',
        'has_file_input': False,
        'validator_class': None,
        'rebuild_data_source_id': None,
    },
    {
        'name': 'XREF Journal Catalog',
        'id': 'xref_journal_catalog',
        'class': 'ivetl.pipelines.rejectedarticles.XREFJournalCatalogPipeline',
        'has_file_input': False,
        'validator_class': None,
        'rebuild_data_source_id': None,
    },
    {
        'name': 'Site Metadata',
        'id': 'site_metadata',
        'user_facing_display_name': 'Site metadata',
        'class': 'ivetl.pipelines.sitemetadata.SiteMetadataPipeline',
        'has_file_input': False,
        'validator_class': None,
        'rebuild_data_source_id': None,
        'hide_demo_filter': True,
        'single_publisher_pipeline': True,
        'single_publisher_id': 'hw',
        'pipeline_run_button_label': 'Update Site and Check Metadata',
    },
    {
        'name': 'Site Uptime',
        'id': 'site_uptime',
        'user_facing_display_name': 'Site uptime',
        'class': 'ivetl.pipelines.siteuptime.SiteUptimePipeline',
        'has_file_input': False,
        'validator_class': None,
        'rebuild_data_source_id': None,
        'hide_demo_filter': True,
        'single_publisher_pipeline': True,
        'single_publisher_id': 'hw',
        'pipeline_run_button_label': 'Update Site Uptime Stats',
        'include_date_range_controls': True,
        'use_high_water_mark': True,
        'supports_restart': True,
    },
    {
        'name': 'Weekly Alerts',
        'id': 'weekly_site_uptime_alerts',
        'user_facing_display_name': 'Weekly Site Uptime Alerts',
        'class': 'ivetl.pipelines.siteuptime.WeeklyAlertsPipeline',
        'has_file_input': False,
        'validator_class': None,
        'rebuild_data_source_id': None,
        'hide_demo_filter': True,
        'single_publisher_pipeline': True,
        'single_publisher_id': 'hw',
        'pipeline_run_button_label': 'Run Weekly Uptime Alerts',
        'include_date_range_controls': False,
        'use_high_water_mark': False,
        'supports_restart': False,
    },
    {
        'name': 'JR2 Institution Usage',
        'id': 'jr2_institution_usage',
        'user_facing_display_name': 'JR2 institution usage',
        'class': 'ivetl.pipelines.institutionusage.JR2InstitutionUsagePipeline',
        'has_file_input': True,
        'validator_class': 'ivetl.validators.JR2Validator',
        'rebuild_data_source_id': None,
    },
    {
        'name': 'JR3 Institution Usage',
        'id': 'jr3_institution_usage',
        'user_facing_display_name': 'JR3 institution usage',
        'class': 'ivetl.pipelines.institutionusage.JR3InstitutionUsagePipeline',
        'has_file_input': True,
        'validator_class': 'ivetl.validators.JR3Validator',
        'rebuild_data_source_id': None,
    },
]
PIPELINE_BY_ID = {p['id']: p for p in PIPELINES}
PIPELINE_CHOICES = [(p['id'], p['name']) for p in PIPELINES]


def get_pipeline_display_name(pipeline):
    user_facing_display_name = pipeline.get('user_facing_display_name')
    if user_facing_display_name:
        return user_facing_display_name.title()
    else:
        pipeline_name = pipeline.get('name')
        if pipeline_name:
            return pipeline_name
        else:
            return pipeline['id']


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
            {
                'pipeline': PIPELINE_BY_ID['article_usage'],
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
            },
            {
                'pipeline': PIPELINE_BY_ID['benchpress_rejected_articles'],
            },
            {
                'pipeline': PIPELINE_BY_ID['reprocess_rejected_articles'],
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
        'order': 5,
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
        'order': 6,
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
        'order': 7,
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
        'order': 8,
        'cohort': False,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['xref_journal_catalog'],
            }
        ],
        'tableau_workbooks': [],
    },
    {
        'name': 'Institutions',
        'id': 'institutions',
        'is_user_facing': True,
        'order': 4,
        'cohort': False,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['jr2_institution_usage'],
            },
            {
                'pipeline': PIPELINE_BY_ID['jr3_institution_usage'],
            },
        ],
        'tableau_workbooks': [],
    },
    {
        'name': 'HighWire Sites',
        'id': 'highwire_sites',
        'is_user_facing': True,
        'order': 5,
        'cohort': False,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['site_metadata'],
            },
            {
                'pipeline': PIPELINE_BY_ID['site_uptime'],
            },
            {
                'pipeline': PIPELINE_BY_ID['weekly_site_uptime_alerts'],
            },
        ],
        'tableau_workbooks': [],
    },
    {
        'name': 'Social',
        'id': 'social',
        'is_user_facing': True,
        'order': 6,
        'cohort': False,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['social_metrics'],
            },
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
        'product_id': 'published_articles',
        'pipeline_id': 'article_usage',
        'ftp_dir_name': 'article_usage_files',
    },
    {
        'product_id': 'rejected_manuscripts',
        'pipeline_id': 'rejected_articles',
        'ftp_dir_name': 'rejected_manuscripts',
    },
    {
        'product_id': 'institutions',
        'pipeline_id': 'jr2_institution_usage',
        'ftp_dir_name': 'jr2_institution_usage_files',
    },
    {
        'product_id': 'institutions',
        'pipeline_id': 'jr3_institution_usage',
        'ftp_dir_name': 'jr3_institution_usage_files',
    },
]
PRODUCT_ID_BY_FTP_DIR_NAME = {f['ftp_dir_name']: f['product_id'] for f in FTP_DIRS}
PIPELINE_ID_BY_FTP_DIR_NAME = {f['ftp_dir_name']: f['pipeline_id'] for f in FTP_DIRS}


def get_ftp_dir_name(product_id, pipeline_id):
    for d in FTP_DIRS:
        if d['product_id'] == product_id and d['pipeline_id'] == pipeline_id:
            return d['ftp_dir_name']
    return None

DEMO_STATUS_CREATING = 'creating'
DEMO_STATUS_SUBMITTED_FOR_REVIEW = 'submitted-for-review'
DEMO_STATUS_CHANGES_NEEDED = 'changes-needed'
DEMO_STATUS_ACCEPTED = 'accepted'
DEMO_STATUS_IN_PROGRESS = 'in-progress'
DEMO_STATUS_COMPLETED = 'completed'
DEMO_STATUS_CHOICES = [
    (DEMO_STATUS_CREATING, 'Creating'),
    (DEMO_STATUS_SUBMITTED_FOR_REVIEW, 'Submitted for Review'),
    (DEMO_STATUS_CHANGES_NEEDED, 'Changes Needed'),
    (DEMO_STATUS_ACCEPTED, 'Accepted'),
    (DEMO_STATUS_IN_PROGRESS, 'In Progress'),
    (DEMO_STATUS_COMPLETED, 'Completed'),
]
DEMO_STATUS_LOOKUP = dict(DEMO_STATUS_CHOICES)

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

PUBLISH_TO_TABLEAU_WHEN_LOCAL = os.environ.get('IVETL_PUBLISH_TO_TABLEAU_WHEN_LOCAL', '0') == '1'

IVETL_WEB_ADDRESS = os.environ.get('IVETL_WEB_ADDRESS', 'http://localhost:8000')

CASSANDRA_IP_LIST = os.environ.get('IVETL_CASSANDRA_IP', '127.0.0.1').split(',')
CASSANDRA_KEYSPACE_IV = os.environ.get('IVETL_CASSANDRA_KEYSPACE', 'impactvizor')

HW_PUBLISHER_ID = 'hw'

BASE_WORKING_DIR = os.environ.get('IVETL_WORKING_DIR', '/iv')
BASE_INCOMING_DIR = os.path.join(BASE_WORKING_DIR, "incoming")
BASE_FTP_DIR = os.path.join(BASE_WORKING_DIR, "ftp")
BASE_WORK_DIR = os.path.join(BASE_WORKING_DIR, "working")
BASE_ARCHIVE_DIR = os.path.join(BASE_WORKING_DIR, "archive")
BASE_DEMO_DIR = os.path.join(BASE_WORKING_DIR, "demos")
TMP_DIR = os.environ.get('IVETL_TMP_DIR', '/iv/tmp')

TABLEAU_SERVER = os.environ.get('IVETL_TABLEAU_SERVER', '10.0.0.143')
TABLEAU_USERNAME = os.environ.get('IVETL_TABLEAU_USERNAME', 'admin')
TABLEAU_PASSWORD = os.environ.get('IVETL_TABLEAU_PASSWORD', 'admin')

MENDELEY_CLIENT_ID = '2474'
MENDELEY_CLIENT_SECRET = '3a9Zm5QXutiCHdqR'

FTP_PUBLIC_IP = os.environ.get('IVFTP_PUBLIC_IP', '127.0.0.1')
RABBITMQ_BROKER_IP = os.environ.get('IVETL_RABBITMQ_BROKER_IP', '127.0.0.1')

EMAIL_TO = os.environ.get('IVETL_EMAIL_TO_ADDRESS', "nmehta@highwire.org")
EMAIL_FROM = os.environ.get('IVETL_EMAIL_FROM_ADDRESS', "impactvizor@highwire.org")
SG_USERNAME = "estacks"
SG_PWD = "Hello123!"

PINGDOM_ACCOUNTS = [
    {
        'name': 'primary',
        'email': 'pingdom@highwire.stanford.edu',
        'password': '#hq77C;_-',
        'api_key': '3j65ak0jedmwy1cu6u68u237a6a47quq'
    },
    {
        'name': 'secondary',
        'email': 'sysadmin@highwire.org',
        'password': '#[~Iw&+J6',
        'api_key': '9jl17p9dka6agqmwb6ru6e7mqt9ei8a1',
    },
]


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
