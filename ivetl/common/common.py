import os
import json
import importlib
import sendgrid
from sendgrid.helpers.mail import Email, Content, Mail, CustomArg, Personalization

with open('/iv/properties.json', 'r') as properties_file:
    ENV_PROPERTIES = json.loads(properties_file.read())

# the IVETL_ROOT env var is mandatory
if 'IVETL_ROOT' not in os.environ:
    print("You must set the IVETL_ROOT env var!")
    exit(1)

IVETL_ROOT = os.environ.get('IVETL_ROOT', '/iv')
IS_LOCAL = os.environ.get('IVETL_LOCAL', '0') == '1'
IS_QA = os.environ.get('IVETL_QA', '0') == '1'
IS_PROD = os.environ.get('IVETL_PROD', '0') == '1'

PIPELINES = [
    {
        'name': 'Published Articles',
        'id': 'published_articles',
        'user_facing_display_name': 'Published articles',
        'visible_on_user_home': True,
        'class': 'ivetl.pipelines.publishedarticles.UpdatePublishedArticlesPipeline',
        'has_file_input': False,
        'validator_class': None,
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.publishedarticles.tasks.GetPublishedArticlesTask',
            'ivetl.pipelines.publishedarticles.tasks.ScopusIdLookupTask',
            'ivetl.pipelines.publishedarticles.tasks.GetHighWireMetadataTask',
            'ivetl.pipelines.publishedarticles.tasks.GetSocialMetricsTask',
            'ivetl.pipelines.publishedarticles.tasks.MendeleyLookupTask',
            'ivetl.pipelines.publishedarticles.tasks.InsertPublishedArticlesIntoCassandra',
            'ivetl.pipelines.publishedarticles.tasks.ResolvePublishedArticlesData',
            'ivetl.pipelines.publishedarticles.tasks.UpdateAttributeValuesCacheTask',
            'ivetl.pipelines.publishedarticles.tasks.ResolveArticleUsageData',
            'ivetl.pipelines.publishedarticles.tasks.CheckRejectedManuscriptTask',
        ],
    },
    {
        'name': 'Refresh Mappings',
        'id': 'refresh_value_mappings',
        'user_facing_display_name': 'Refresh mappings',
        'visible_on_user_home': True,
        'class': 'ivetl.pipelines.publishedarticles.RefreshValueMappingsPipeline',
        'has_file_input': False,
        'validator_class': None,
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.publishedarticles.tasks.ResolvePublishedArticlesData',
            'ivetl.pipelines.publishedarticles.tasks.UpdateAttributeValuesCacheTask',
        ],
    },
    {
        'name': 'Custom Article Data',
        'id': 'custom_article_data',
        'user_facing_display_name': 'Additional article metadata',
        'use_uploaded_instead_of_updated': True,
        'visible_on_user_home': True,
        'class': 'ivetl.pipelines.customarticledata.CustomArticleDataPipeline',
        'has_file_input': True,
        'user_facing_file_description': 'Article Metadata',
        'validator_class': 'ivetl.validators.CustomArticleDataValidator',
        'format_file': 'AdditionalMetadata-Format.pdf',
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.customarticledata.tasks.GetArticleDataFiles',
            'ivetl.pipelines.customarticledata.tasks.ValidateArticleDataFiles',
            'ivetl.pipelines.customarticledata.tasks.InsertCustomArticleDataIntoCassandra',
            'ivetl.pipelines.publishedarticles.tasks.ResolvePublishedArticlesData',
            'ivetl.pipelines.publishedarticles.tasks.UpdateAttributeValuesCacheTask',
        ],
    },
    {
        'name': 'Article Citations',
        'id': 'article_citations',
        'user_facing_display_name': 'Article citations',
        'visible_on_user_home': True,
        'class': 'ivetl.pipelines.articlecitations.UpdateArticleCitationsPipeline',
        'has_file_input': False,
        'validator_class': None,
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.articlecitations.tasks.GetScopusArticleCitations',
            'ivetl.pipelines.articlecitations.tasks.InsertScopusIntoCassandra',
            'ivetl.pipelines.articlecitations.tasks.UpdateArticleCitationsWithCrossref',
        ],
    },
    {
        'name': 'Article Usage',
        'id': 'article_usage',
        'user_facing_display_name': 'Article usage',
        'visible_on_user_home': True,
        'class': 'ivetl.pipelines.articleusage.ArticleUsagePipeline',
        'has_file_input': True,
        'user_facing_file_description': 'Article Usage',
        'validator_class': 'ivetl.validators.ArticleUsageValidator',
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.articleusage.tasks.GetArticleUsageFiles',
            'ivetl.pipelines.articleusage.tasks.ValidateArticleUsageFiles',
            'ivetl.pipelines.articleusage.tasks.InsertArticleUsageIntoCassandra',
            'ivetl.pipelines.publishedarticles.tasks.ResolveArticleUsageData',
        ],
    },
    {
        'name': 'Social Metrics',
        'id': 'social_metrics',
        'user_facing_display_name': 'Social metrics',
        'visible_on_user_home': True,
        'class': 'ivetl.pipelines.socialmetrics.SocialMetricsPipeline',
        'has_file_input': False,
        'validator_class': None,
        'hide_demo_filter': True,
        'single_publisher_pipeline': True,
        'single_publisher_id': 'hw',
        'pipeline_run_button_label': 'Get Latest Social Metrics',
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.socialmetrics.tasks.LoadAltmetricsDataTask',
            'ivetl.pipelines.socialmetrics.tasks.LoadF1000DataTask',
        ],
    },
    {
        'name': 'Upload Rejected',
        'id': 'rejected_articles',
        'user_facing_display_name': 'Manuscripts imported from files',
        'use_colon_instead_of_updated': True,
        'visible_on_user_home': True,
        'class': 'ivetl.pipelines.rejectedarticles.UpdateRejectedArticlesPipeline',
        'has_file_input': True,
        'user_facing_file_description': 'Rejected Manuscripts',
        'validator_class': 'ivetl.validators.RejectedArticlesValidator',
        'format_file': 'RejectedArticles-Format.pdf',
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.rejectedarticles.tasks.GetRejectedArticlesDataFiles',
            'ivetl.pipelines.rejectedarticles.tasks.ValidateInputFileTask',
            'ivetl.pipelines.rejectedarticles.tasks.PrepareInputFileTask',
            'ivetl.pipelines.rejectedarticles.tasks.XREFPublishedArticleSearchTask',
            'ivetl.pipelines.rejectedarticles.tasks.ScopusCitationLookupTask',
            'ivetl.pipelines.rejectedarticles.tasks.MendeleyLookupTask',
            'ivetl.pipelines.rejectedarticles.tasks.PrepareForDBInsertTask',
            'ivetl.pipelines.rejectedarticles.tasks.InsertIntoCassandraDBTask',
            'ivetl.pipelines.publishedarticles.tasks.CheckRejectedManuscriptTask',
        ],
    },
    {
        'name': 'Bench Press Rejected',
        'id': 'benchpress_rejected_articles',
        'user_facing_display_name': 'Manuscripts imported from BenchPress',
        'use_colon_instead_of_updated': True,
        'visible_on_user_home': True,
        'class': 'ivetl.pipelines.rejectedarticles.GetRejectedArticlesFromBenchPressPipeline',
        'has_file_input': False,
        'include_date_range_controls': True,
        'filter_for_benchpress_support': True,
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.rejectedarticles.tasks.GetRejectedArticlesFromBenchPressTask',
            'ivetl.pipelines.rejectedarticles.tasks.ParseBenchPressFileTask',
            'ivetl.pipelines.rejectedarticles.tasks.XREFPublishedArticleSearchTask',
            'ivetl.pipelines.rejectedarticles.tasks.ScopusCitationLookupTask',
            'ivetl.pipelines.rejectedarticles.tasks.MendeleyLookupTask',
            'ivetl.pipelines.rejectedarticles.tasks.PrepareForDBInsertTask',
            'ivetl.pipelines.rejectedarticles.tasks.InsertIntoCassandraDBTask',
            'ivetl.pipelines.publishedarticles.tasks.CheckRejectedManuscriptTask',
        ],
    },
    {
        'name': 'Reprocess Rejected',
        'id': 'reprocess_rejected_articles',
        'user_facing_display_name': 'Published status for all manuscripts',
        'visible_on_user_home': True,
        'class': 'ivetl.pipelines.rejectedarticles.ReprocessRejectedArticlesPipeline',
        'has_file_input': False,
        'validator_class': None,
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.rejectedarticles.tasks.GetRejectedArticlesTask',
            'ivetl.pipelines.rejectedarticles.tasks.XREFPublishedArticleSearchTask',
            'ivetl.pipelines.rejectedarticles.tasks.ScopusCitationLookupTask',
            'ivetl.pipelines.rejectedarticles.tasks.MendeleyLookupTask',
            'ivetl.pipelines.rejectedarticles.tasks.PrepareForDBInsertTask',
            'ivetl.pipelines.rejectedarticles.tasks.InsertIntoCassandraDBTask',
            'ivetl.pipelines.publishedarticles.tasks.CheckRejectedManuscriptTask',
        ],
    },
    {
        'name': 'Check Rejected Manuscripts',
        'id': 'check_rejected_manuscripts',
        'class': 'ivetl.pipelines.publishedarticles.CheckRejectedManuscriptsPipeline',
        'has_file_input': False,
        'validator_class': None,
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.publishedarticles.tasks.CheckRejectedManuscriptTask',
        ],
    },
    {
        'name': 'Insert Placeholder Citations',
        'id': 'insert_placeholder_citations',
        'class': 'ivetl.pipelines.publishedarticles.InsertPlaceholderCitationsPipeline',
        'has_file_input': False,
        'validator_class': None,
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.publishedarticles.tasks.InsertPlaceholderCitationsIntoCassandraTask',
        ],
    },
    {
        'name': 'Update Manuscripts',
        'id': 'update_manuscripts',
        'class': 'ivetl.pipelines.rejectedarticles.UpdateManuscriptsPipeline',
        'has_file_input': False,
        'validator_class': None,
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.rejectedarticles.tasks.UpdateManuscriptsInCassandraTask',
        ],
    },
    {
        'name': 'XREF Journal Catalog',
        'id': 'xref_journal_catalog',
        'class': 'ivetl.pipelines.rejectedarticles.XREFJournalCatalogPipeline',
        'has_file_input': False,
        'validator_class': None,
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.rejectedarticles.tasks.UpdateManuscriptsInCassandraTask',
        ],
    },
    {
        'name': 'Site Metadata',
        'id': 'site_metadata',
        'user_facing_display_name': 'Site metadata',
        'class': 'ivetl.pipelines.sitemetadata.SiteMetadataPipeline',
        'has_file_input': False,
        'validator_class': None,
        'hide_demo_filter': True,
        'single_publisher_pipeline': True,
        'single_publisher_id': 'hw',
        'pipeline_run_button_label': 'Update Site and Check Metadata',
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.sitemetadata.tasks.LoadH20MetadataTask',
            'ivetl.pipelines.sitemetadata.tasks.LoadDrupalMetadataTask',
            'ivetl.pipelines.sitemetadata.tasks.GetChecksTask',
            'ivetl.pipelines.sitemetadata.tasks.ClassifyChecksTask',
            'ivetl.pipelines.sitemetadata.tasks.InsertChecksIntoCassandraTask',
            'ivetl.pipelines.sitemetadata.tasks.UpdateAttributeValuesCacheTask',
        ],
    },
    {
        'name': 'Site Uptime',
        'id': 'site_uptime',
        'user_facing_display_name': 'Site uptime',
        'class': 'ivetl.pipelines.siteuptime.SiteUptimePipeline',
        'has_file_input': False,
        'validator_class': None,
        'hide_demo_filter': True,
        'single_publisher_pipeline': True,
        'single_publisher_id': 'hw',
        'pipeline_run_button_label': 'Update Site Uptime Stats',
        'include_date_range_controls': True,
        'use_high_water_mark': True,
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.siteuptime.tasks.GetUptimeStatsTask',
            'ivetl.pipelines.siteuptime.tasks.InsertStatsIntoCassandraTask',
        ],
    },
    {
        'name': 'Weekly Alerts',
        'id': 'weekly_site_uptime_alerts',
        'user_facing_display_name': 'Weekly Site Uptime Alerts',
        'class': 'ivetl.pipelines.siteuptime.WeeklyAlertsPipeline',
        'has_file_input': False,
        'validator_class': None,
        'hide_demo_filter': True,
        'single_publisher_pipeline': True,
        'single_publisher_id': 'hw',
        'pipeline_run_button_label': 'Run Weekly Uptime Alerts',
        'include_date_range_controls': False,
        'use_high_water_mark': False,
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.siteuptime.tasks.RunWeeklyAlertsTask',
        ],
    },
    {
        'name': 'JR2 Institution Usage',
        'id': 'jr2_institution_usage',
        'user_facing_display_name': 'JR2 usage',
        'visible_on_user_home': True,
        'class': 'ivetl.pipelines.institutionusage.JR2InstitutionUsagePipeline',
        'has_file_input': True,
        'hide_upload_from_user_home': True,
        'user_facing_file_description': 'JR2 Institution Usage',
        'validator_class': 'ivetl.validators.JR2Validator',
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.institutionusage.tasks.GetJR2FilesTask',
            'ivetl.pipelines.institutionusage.tasks.ValidateJR2FilesTask',
            'ivetl.pipelines.institutionusage.tasks.InsertJR2IntoCassandraTask',
        ],
    },
    {
        'name': 'JR3 Institution Usage',
        'id': 'jr3_institution_usage',
        'user_facing_display_name': 'JR3 usage',
        'visible_on_user_home': True,
        'class': 'ivetl.pipelines.institutionusage.JR3InstitutionUsagePipeline',
        'has_file_input': True,
        'hide_upload_from_user_home': True,
        'user_facing_file_description': 'JR3 Institution Usage',
        'validator_class': 'ivetl.validators.JR3Validator',
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.institutionusage.tasks.GetJR3FilesTask',
            'ivetl.pipelines.institutionusage.tasks.ValidateJR3FilesTask',
            'ivetl.pipelines.institutionusage.tasks.InsertJR3IntoCassandraTask',
            'ivetl.pipelines.productbundles.tasks.UpdateInstitutionUsageStatsTask',
        ],
    },
    {
        'name': 'Service Stats',
        'id': 'service_stats',
        'user_facing_display_name': 'Service stats',
        'class': 'ivetl.pipelines.servicestats.ServiceStatsPipeline',
        'has_file_input': False,
        'validator_class': None,
        'hide_demo_filter': True,
        'single_publisher_pipeline': True,
        'single_publisher_id': 'hw',
        'pipeline_run_button_label': 'Update Service Stats',
        'include_date_range_controls': True,
        'use_high_water_mark': True,
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.servicestats.tasks.GetStatsFilesTask',
            'ivetl.pipelines.servicestats.tasks.InsertStatsIntoCassandraTask',
        ],
    },
    {
        'name': 'Bundle Definitions',
        'id': 'bundle_definitions',
        'user_facing_display_name': 'Product bundles',
        'use_uploaded_instead_of_updated': True,
        'visible_on_user_home': True,
        'class': 'ivetl.pipelines.productbundles.BundleDefinitionsPipeline',
        'has_file_input': True,
        'user_facing_file_description': 'Bundle Definitions',
        'validator_class': 'ivetl.validators.BundleDefinitionsValidator',
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.productbundles.tasks.GetBundleDefinitionsFilesTask',
            'ivetl.pipelines.productbundles.tasks.ValidateBundleDefinitionsFilesTask',
            'ivetl.pipelines.productbundles.tasks.InsertBundleDefinitionsIntoCassandraTask',
            'ivetl.pipelines.productbundles.tasks.UpdateInstitutionUsageStatsTask',
        ],
    },
    {
        'name': 'Subscription Pricing',
        'id': 'subscription_pricing',
        'user_facing_display_name': 'Subscription pricing',
        'use_uploaded_instead_of_updated': True,
        'visible_on_user_home': True,
        'class': 'ivetl.pipelines.productbundles.SubscriptionPricingPipeline',
        'has_file_input': True,
        'user_facing_file_description': 'Subsciption Pricing',
        'validator_class': 'ivetl.validators.SubscriptionPricingValidator',
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.productbundles.tasks.GetSubscriptionPricingFilesTask',
            'ivetl.pipelines.productbundles.tasks.ValidateSubscriptionPricingFilesTask',
            'ivetl.pipelines.productbundles.tasks.InsertSubscriptionPricingIntoCassandraTask',
            'ivetl.pipelines.productbundles.tasks.UpdateInstitutionUsageStatsTask',
        ],
    },
    {
        'name': 'Subscription Data',
        'id': 'subscribers_and_subscriptions',
        'user_facing_display_name': 'HighWire subscribers',
        'visible_on_user_home': False,
        'class': 'ivetl.pipelines.subscriberdata.SubscribersAndSubscriptionsPipeline',
        'has_file_input': False,
        'validator_class': None,
        'hide_demo_filter': True,
        'single_publisher_pipeline': True,
        'single_publisher_id': 'hw',
        'pipeline_run_button_label': 'Load Subscriber and Subscription Data',
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.subscriberdata.tasks.LoadSubscriberDataTask',
            'ivetl.pipelines.subscriberdata.tasks.LoadSubscriptionDataTask',
            'ivetl.pipelines.subscriberdata.tasks.ResolveSubscriberDataTask',
        ],
    },
    {
        'name': 'Custom Subscriber Data',
        'id': 'custom_subscriber_data',
        'user_facing_display_name': 'Additional subscriber metadata',
        'use_uploaded_instead_of_updated': True,
        'visible_on_user_home': True,
        'class': 'ivetl.pipelines.customsubscriberdata.CustomSubscriberDataPipeline',
        'has_file_input': True,
        'user_facing_file_description': 'Additional Subscriber Data',
        'validator_class': 'ivetl.validators.CustomSubscriberDataValidator',
        'format_file': 'AdditionalSubscriberData-Format.pdf',
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.customsubscriberdata.tasks.GetSubscriberDataFilesTask',
            'ivetl.pipelines.customsubscriberdata.tasks.ValidateSubscriberDataFilesTask',
            'ivetl.pipelines.customsubscriberdata.tasks.InsertCustomSubscriberDataIntoCassandraTask',
            'ivetl.pipelines.subscriberdata.tasks.ResolveSubscriberDataTask',
        ],
    },
    {
        'name': 'Institution Usage Deltas',
        'id': 'update_institution_usage_deltas',
        'user_facing_display_name': 'Institution usage deltas',
        'class': 'ivetl.pipelines.institutionusagedeltas.UpdateDeltasPipeline',
        'has_file_input': False,
        'supports_restart': True,
        'include_date_range_controls': True,
        'tasks': [
            'ivetl.pipelines.institutionusagedeltas.tasks.UpdateDeltasTask',
        ],
    },
    {
        'name': 'Cost-Per-Use Deltas',
        'id': 'update_subscription_cost_per_use_deltas',
        'user_facing_display_name': 'Subscription cost-per-use deltas',
        'class': 'ivetl.pipelines.subscriptioncostperusedeltas.UpdateDeltasPipeline',
        'has_file_input': False,
        'supports_restart': True,
        'tasks': [
            'ivetl.pipelines.subscriptioncostperusedeltas.tasks.UpdateCostPerUseTask',
            'ivetl.pipelines.subscriptioncostperusedeltas.tasks.UpdateBundleDeltasTask',
            'ivetl.pipelines.subscriptioncostperusedeltas.tasks.UpdateSubscriberDeltasTask',
        ],
    },
]  # type: list[dict]
PIPELINE_BY_ID = {p['id']: p for p in PIPELINES}
PIPELINE_CHOICES = [(p['id'], p['name']) for p in PIPELINES]

CHAINS = [
    {
        'id': 'usage_chain',
        'source_pipelines': [
            ('institutions', 'jr3_institution_usage'),
            ('institutions', 'bundle_definitions'),
            ('institutions', 'subscription_pricing'),
        ],
        'dependent_pipelines': [
            ('institutions', 'update_institution_usage_deltas'),
            ('institutions', 'update_subscription_cost_per_use_deltas'),
        ]
    }
]  # type: list[dict]
CHAIN_BY_ID = {c['id']: c for c in CHAINS}
CHAINS_BY_SOURCE_PIPELINE = {}
for chain in CHAINS:
    for pipeline_tuple in chain['source_pipelines']:
        if pipeline_tuple not in CHAINS_BY_SOURCE_PIPELINE:
            CHAINS_BY_SOURCE_PIPELINE[pipeline_tuple] = []
        CHAINS_BY_SOURCE_PIPELINE[pipeline_tuple].append(chain['id'])


def get_pipeline_class(pipeline):
    pipeline_module_name, class_name = pipeline['class'].rsplit('.', 1)
    return getattr(importlib.import_module(pipeline_module_name), class_name)


def get_task_class(task_class_path):
    task_module_name, class_name = task_class_path.rsplit('.', 1)
    return getattr(importlib.import_module(task_module_name), class_name)


def get_validator_class(pipeline):
    validator_module_name, class_name = pipeline['validator_class'].rsplit('.', 1)
    return getattr(importlib.import_module(validator_module_name), class_name)


def task_id_from_path(task_class_path):
    return task_class_path[task_class_path.rfind('.') + 1:]


PRODUCTS = [
    {
        'name': 'Rejected Manuscripts',
        'id': 'rejected_manuscripts',
        'icon': 'lnr-layers-crossed',
        'is_user_facing': True,
        'order': 1,
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
    },
    {
        'name': 'Published Articles',
        'id': 'published_articles',
        'icon': 'lnr-layers',
        'is_user_facing': True,
        'order': 2,
        'cohort': False,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['published_articles'],
            },
            {
                'pipeline': PIPELINE_BY_ID['article_usage'],
            },
            {
                'pipeline': PIPELINE_BY_ID['custom_article_data'],
            },
            {
                'pipeline': PIPELINE_BY_ID['refresh_value_mappings'],
            },
        ],
    },
    {
        'name': 'Article Citations',
        'id': 'article_citations',
        'icon': 'lnr-layers',
        'is_user_facing': True,
        'order': 3,
        'cohort': False,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['article_citations'],
            },
        ],
    },
    {
        'name': 'Cohort Articles',
        'id': 'cohort_articles',
        'icon': 'lnr-icons2',
        'is_user_facing': True,
        'order': 4,
        'cohort': True,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['published_articles'],
            },
        ],
    },
    {
        'name': 'Cohort Citations',
        'id': 'cohort_citations',
        'icon': 'lnr-icons2',
        'is_user_facing': True,
        'order': 6,
        'cohort': True,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['article_citations'],
            },
        ],
    },
    {
        'name': 'Check Rejected Manuscripts',
        'id': 'check_rejected_manuscripts',
        'is_user_facing': False,
        'order': 7,
        'cohort': False,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['check_rejected_manuscripts'],
            }
        ],
    },
    {
        'name': 'Insert Placeholder Citations',
        'id': 'insert_placeholder_citations',
        'is_user_facing': False,
        'order': 8,
        'cohort': False,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['insert_placeholder_citations'],
            }
        ],
    },
    {
        'name': 'Update Manuscripts',
        'id': 'update_manuscripts',
        'is_user_facing': False,
        'order': 9,
        'cohort': False,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['update_manuscripts'],
            }
        ],
    },
    {
        'name': 'XREF Journal Catalog',
        'id': 'xref_journal_catalog',
        'is_user_facing': False,
        'order': 10,
        'cohort': False,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['xref_journal_catalog'],
            }
        ],
    },
    {
        'name': 'Institutions',
        'id': 'institutions',
        'is_user_facing': True,
        'icon': 'lnr-reading',
        'order': 11,
        'cohort': False,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['jr2_institution_usage'],
            },
            {
                'pipeline': PIPELINE_BY_ID['jr3_institution_usage'],
            },
            {
                'pipeline': PIPELINE_BY_ID['subscribers_and_subscriptions'],
            },
            {
                'pipeline': PIPELINE_BY_ID['custom_subscriber_data'],
            },
            {
                'pipeline': PIPELINE_BY_ID['bundle_definitions'],
            },
            {
                'pipeline': PIPELINE_BY_ID['subscription_pricing'],
            },
            {
                'pipeline': PIPELINE_BY_ID['update_institution_usage_deltas'],
            },
            {
                'pipeline': PIPELINE_BY_ID['update_subscription_cost_per_use_deltas'],
            },
        ],
    },
    {
        'name': 'HighWire Sites',
        'id': 'highwire_sites',
        'is_user_facing': True,
        'order': 12,
        'cohort': False,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['site_metadata'],
            },
            {
                'pipeline': PIPELINE_BY_ID['site_uptime'],
            },
            {
                'pipeline': PIPELINE_BY_ID['service_stats'],
            },
            {
                'pipeline': PIPELINE_BY_ID['weekly_site_uptime_alerts'],
            },
        ],
    },
    {
        'name': 'Social',
        'id': 'social',
        'is_user_facing': True,
        'order': 13,
        'cohort': False,
        'pipelines': [
            {
                'pipeline': PIPELINE_BY_ID['social_metrics'],
            },
        ],
    },
]  # type: list[dict]
PRODUCT_BY_ID = {p['id']: p for p in PRODUCTS}
PRODUCT_CHOICES = [(p['id'], p['name']) for p in PRODUCTS]

PRODUCT_GROUPS = [
    {
        'name': 'ImpactVizor',
        'id': 'impact_vizor',
        'products': [
            'published_articles',
            'article_citations',
            'rejected_manuscripts',
            'cohort_articles',
            'cohort_citations',
        ],
        'tableau_datasources': [
            'article_citations_ds.tds',
            'article_usage_ds.tds',
            'rejected_articles_ds.tds',
        ],
        'tableau_workbooks': [
            'advance_correlator_citation_usage.twb',
            'alert_advance_correlator_citation_usage_configure.twb',
            'alert_advance_correlator_citation_usage_export.twb',
            'citation_distribution_surveyor.twb',
            'cohort_comparator.twb',
            'hot_article_tracker.twb',
            'alert_hot_article_tracker_configure.twb',
            'alert_hot_article_tracker_export.twb',
            'hot_object_tracker.twb',
            'rejected_article_tracker.twb',
            'alert_rejected_article_tracker_configure.twb',
            'alert_rejected_article_tracker_export.twb',
            'section_performance_analyzer.twb',
        ],
    },
    {
        'name': 'UsageVizor',
        'id': 'usage_vizor',
        'products': [
            'published_articles',
            'institutions',
        ],
        'tableau_datasources': [
            'inst_usage_ds.tds',
            'subscriber_ds.tds',
            'subscriptions_ds.tds',
            'inst_usage_delta_ds.tds',
            'subscription_pricing_ds.tds',
            'cost_by_subscriber_bundle_ds.tds',
            'cost_delta_subscriber_bundle_ds.tds',
            'article_usage_with_article_metadata_ds.tds',
        ],
        'tableau_workbooks': [
            'uv_institutional_usage.twb',
            'alert_uv_institutional_usage_export.twb',
            'uv_article_usage.twb',
        ]
    },
    {
        'name': 'SocialVizor',
        'id': 'social_vizor',
        'products': [
            'published_articles',
            'social',
        ],
        'tableau_datasources': [],
        'tableau_workbooks': [],
    },
]
PRODUCT_GROUP_BY_ID = {p['id']: p for p in PRODUCT_GROUPS}

TABLEAU_WORKBOOKS = [
    {
        'id': 'rejected_article_tracker.twb',
        'name': 'Rejected Article Tracker',
        'home_view': 'Overview',
    },
    {
        'id': 'alert_rejected_article_tracker_configure.twb',
        'name': 'alert_rejected_article_tracker_configure',
        'home_view': 'Overview',
        'admin_only': True,
    },
    {
        'id': 'alert_rejected_article_tracker_export.twb',
        'name': 'alert_rejected_article_tracker_export',
        'home_view': 'Inspector',
        'admin_only': True,
    },
    {
        'id': 'section_performance_analyzer.twb',
        'name': 'Section Performance Analyzer',
        'home_view': 'Overview',
    },
    {
        'id': 'hot_article_tracker.twb',
        'name': 'Hot Article Tracker',
        'home_view': 'HotArticleTracker',
    },
    {
        'id': 'alert_hot_article_tracker_configure.twb',
        'name': 'alert_hot_article_tracker_configure',
        'home_view': 'Overview',
        'admin_only': True,
    },
    {
        'id': 'alert_hot_article_tracker_export.twb',
        'name': 'alert_hot_article_tracker_export',
        'home_view': 'Inspector',
        'admin_only': True,
    },
    {
        'id': 'hot_object_tracker.twb',
        'name': 'Hot Object Tracker',
        'home_view': 'Overview',
    },
    {
        'id': 'citation_distribution_surveyor.twb',
        'name': 'Citation Distribution Surveyor',
        'home_view': 'Overview',
    },
    {
        'id': 'advance_correlator_citation_usage.twb',
        'name': 'Advance Correlator of Citations & Usage',
        'home_view': 'Section-to-SectionComparator',
    },
    {
        'id': 'alert_advance_correlator_citation_usage_configure.twb',
        'name': 'alert_advance_correlator_citation_usage_configure',
        'home_view': 'Overview',
        'admin_only': True,
    },
    {
        'id': 'alert_advance_correlator_citation_usage_export.twb',
        'name': 'alert_advance_correlator_citation_usage_export',
        'home_view': 'Inspector',
        'admin_only': True,
    },
    {
        'id': 'cohort_comparator.twb',
        'name': 'Cohort Comparator',
        'home_view': 'Overview',
    },
    {
        'id': 'uv_institutional_usage.twb',
        'name': 'UV: Institutional Usage',
        'home_view': 'Overview',
    },
    {
        'id': 'alert_uv_institutional_usage_export.twb',
        'name': 'alert_uv_institutional_usage_export',
        'home_view': 'Overview',
        'admin_only': True,
    },
    {
        'id': 'uv_article_usage.twb',
        'name': 'UV: Article Usage',
        'home_view': 'Overview',
    },
]  # type: list[dict]

TABLEAU_WORKBOOKS_BY_ID = {w['id']: w for w in TABLEAU_WORKBOOKS}
TABLEAU_WORKBOOKS_BY_NAME = {w['name']: w for w in TABLEAU_WORKBOOKS}
TABLEAU_DATASOURCE_FILE_EXTENSION = '.tds'
TABLEAU_WORKBOOK_FILE_EXTENSION = '.twb'
TABLEAU_TEMPLATE_PUBLISHER_ID_TO_REPLACE = 'blood'
TABLEAU_TEMPLATE_SERVER_TO_REPLACE = 'vizors.stackly.org'
TABLEAU_DUMMY_EXTRACTS_DIR_NAME = 'dummy_extracts'
TABCMD = os.path.join(IVETL_ROOT, 'deploy/tabcmd/tabcmd.sh')

TABLEAU_DATASOURCE_UPDATES = {
    ('published_articles', 'article_usage'): [
        'article_citations_ds.tds',
        'article_usage_ds.tds',
        'article_usage_with_article_metadata_ds.tds',
    ],
    ('published_articles', 'refresh_value_mappings'): [
        'article_citations_ds.tds',
        'article_usage_with_article_metadata_ds.tds',
    ],
    ('published_articles', 'custom_article_data'): [
        'article_citations_ds.tds',
        'article_usage_with_article_metadata_ds.tds',
    ],
    ('article_citations', 'article_citations'): [
        'article_citations_ds.tds'
    ],
    ('rejected_manuscripts', 'rejected_articles'): [
        'rejected_articles_ds.tds'
    ],
    ('rejected_manuscripts', 'benchpress_rejected_articles'): [
        'rejected_articles_ds.tds'
    ],
    ('rejected_manuscripts', 'reprocess_rejected_articles'): [
        'rejected_articles_ds.tds'
    ],
    ('cohort_citations', 'article_citations'): [
        'article_citations_ds.tds'
    ],
    ('institutions', 'subscribers_and_subscriptions'): [
        'subscriptions_ds.tds'
        'subscriber_ds.tds'
    ],
    ('institutions', 'custom_subscriber_data'): [
        'subscriber_ds.tds',
    ],
    ('institutions', 'update_institution_usage_deltas'): [
        'inst_usage_ds.tds',
        'inst_usage_delta_ds.tds',
        'subscription_pricing_ds.tds',
        'cost_by_subscriber_bundle_ds.tds',
        'cost_delta_subscriber_bundle_ds.tds',
    ],
    ('institutions', 'update_subscription_cost_per_use_deltas'): [
        'inst_usage_ds.tds',
        'inst_usage_delta_ds.tds',
        'subscription_pricing_ds.tds',
        'cost_by_subscriber_bundle_ds.tds',
        'cost_delta_subscriber_bundle_ds.tds',
    ],
}

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
    {
        'product_id': 'institutions',
        'pipeline_id': 'bundle_definitions',
        'ftp_dir_name': 'bundle_definitions',
    },
    {
        'product_id': 'institutions',
        'pipeline_id': 'subscription_pricing',
        'ftp_dir_name': 'subscription_pricing',
    },
    {
        'product_id': 'institutions',
        'pipeline_id': 'custom_subscriber_data',
        'ftp_dir_name': 'additional_subscriber_data_files',
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

DEBUG_QUICKLY = bool(os.environ.get('IVETL_DEBUG_QUICKLY', False))

PUBLISH_TO_TABLEAU = os.environ.get('IVETL_PUBLISH_TO_TABLEAU', '1') == '1'

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

HWDW_METADATA_BUCKET = os.environ.get('IVETL_HWDW_METADATA_BUCKET', 'hwdw-metadata')
AWS_ACCESS_KEY_ID = ENV_PROPERTIES['aws']['access_key_id']
AWS_SECRET_ACCESS_KEY = ENV_PROPERTIES['aws']['secret_access_key']

TABLEAU_SERVER = os.environ.get('IVETL_TABLEAU_SERVER', '10.0.0.143')
TABLEAU_IP = os.environ.get('IVETL_TABLEAU_IP', '10.0.0.143')
TABLEAU_HTTPS = os.environ.get('IVETL_TABLEAU_HTTPS', '0') == '1'
TABLEAU_USERNAME = os.environ.get('IVETL_TABLEAU_USERNAME', 'admin')
TABLEAU_PASSWORD = os.environ.get('IVETL_TABLEAU_PASSWORD', 'admin')

MENDELEY_CLIENT_ID = '2474'
MENDELEY_CLIENT_SECRET = '3a9Zm5QXutiCHdqR'

FTP_PUBLIC_IP = os.environ.get('IVFTP_PUBLIC_IP', '127.0.0.1')
RABBITMQ_BROKER_URL = os.environ.get('IVETL_RABBITMQ_BROKER_URL', 'amqp://guest:guest@127.0.0.1:5672//')

RATE_LIMITER_SERVER = os.environ.get('IVETL_RATE_LIMITER_SERVER', '127.0.0.1:8082')

EMAIL_TO = os.environ.get('IVETL_EMAIL_TO_ADDRESS', "nmehta@highwire.org")
EMAIL_FROM = os.environ.get('IVETL_EMAIL_FROM_ADDRESS', "impactvizor@highwire.org")
SG_USERNAME = "estacks"
SG_PWD = "Hello123!"
SG_API_KEY = "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"

FTP_ADMIN_BCC = 'vizor-support@highwire.org'

NETSITE_USERNAME = ENV_PROPERTIES['netsite']['username']
NETSITE_PASSWORD = ENV_PROPERTIES['netsite']['password']

PINGDOM_ACCOUNTS = [
    {
        'name': 'primary',
        'email': 'pingdom@highwire.stanford.edu',
        'password': ENV_PROPERTIES['pingdom']['primary']['password'],
        'api_key': '3j65ak0jedmwy1cu6u68u237a6a47quq'
    },
    {
        'name': 'secondary',
        'email': 'sysadmin@highwire.org',
        'password': ENV_PROPERTIES['pingdom']['secondary']['password'],
        'api_key': '9jl17p9dka6agqmwb6ru6e7mqt9ei8a1',
    },
]


def send_email(subject, body, to=EMAIL_TO, bcc=None, email_format="text/html", custom_args=None):
    sg = sendgrid.SendGridAPIClient(apikey=SG_API_KEY)
    from_email = Email(EMAIL_FROM)
    to_email = Email(to)
    content = Content(email_format, body)
    mail = Mail(from_email, subject, to_email, content)
    personalization = Personalization()

    use_personalization = False

    if bcc:
        personalization.add_bcc(Email(bcc))
        use_personalization = True

    if custom_args:
        for key, value in custom_args.items():
            mail.add_custom_arg(CustomArg(key, value))
        use_personalization = True

    if use_personalization:
        mail.add_personalization(personalization)

    response = sg.client.mail.send.post(request_body=mail.get())
    return response
