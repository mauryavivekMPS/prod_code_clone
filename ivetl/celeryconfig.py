import os
from celery.schedules import crontab
from ivetl.common import common

BROKER_URL = common.RABBITMQ_BROKER_URL

CELERY_IMPORTS = (
    'ivetl.pipelines.publishedarticles',
    'ivetl.pipelines.publishedarticles.tasks',
    'ivetl.pipelines.customarticledata',
    'ivetl.pipelines.customarticledata.tasks',
    'ivetl.pipelines.articlecitations',
    'ivetl.pipelines.articlecitations.tasks',
    'ivetl.pipelines.mendeleysaves',
    'ivetl.pipelines.mendeleysaves.tasks',
    'ivetl.pipelines.rejectedarticles',
    'ivetl.pipelines.rejectedarticles.tasks',
    'ivetl.pipelines.articleusage',
    'ivetl.pipelines.articleusage.tasks',
    'ivetl.pipelines.sitemetadata',
    'ivetl.pipelines.sitemetadata.tasks',
    'ivetl.pipelines.siteuptime',
    'ivetl.pipelines.siteuptime.tasks',
    'ivetl.pipelines.institutionusage',
    'ivetl.pipelines.institutionusage.tasks',
    'ivetl.pipelines.socialmetrics',
    'ivetl.pipelines.socialmetrics.tasks',
    'ivetl.pipelines.servicestats',
    'ivetl.pipelines.servicestats.tasks',
    'ivetl.pipelines.subscriberdata',
    'ivetl.pipelines.subscriberdata.tasks',
    'ivetl.pipelines.customsubscriberdata',
    'ivetl.pipelines.customsubscriberdata.tasks',
    'ivetl.pipelines.productbundles',
    'ivetl.pipelines.productbundles.tasks',
    'ivetl.pipelines.institutionusagedeltas',
    'ivetl.pipelines.institutionusagedeltas.tasks',
    'ivetl.pipelines.subscriptioncostperusedeltas',
    'ivetl.pipelines.subscriptioncostperusedeltas.tasks',
    'ivetl.pipelines.metapredictions',
    'ivetl.pipelines.metapredictions.tasks',
    'ivetl.tasks',
)

CELERY_TASK_RESULT_EXPIRES = 3600
CELERY_ACKS_LATE = False
CELERYD_PREFETCH_MULTIPLIER = 1
CELERY_TRACK_STARTED = False
CELERY_SEND_TASK_ERROR_EMAILS = True

# Name and email addresses of recipients
ADMINS = (
    ('IVETL Admin', os.environ.get('IVETL_EMAIL_TO_ADDRESS', "vizor-developers@highwirepress.com")),
)

# Email address used as sender (From field).
SERVER_EMAIL = 'impactvizor@highwire.org'

# Mailserver configuration
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'estacks'
EMAIL_HOST_PASSWORD = 'Hello123!'

CELERYBEAT_SCHEDULE = {
    'get-uptime-metadata-every-morning-at-2am': {
        'task': 'ivetl.pipelines.sitemetadata.site_metadata_pipeline.SiteMetadataPipeline',
        'schedule': crontab(hour=2, minute=0),
        'kwargs': {'product_id': 'highwire_sites'},
    },
    # 'get-service-stats-every-morning-at-2-10am': {
    #     'task': 'ivetl.pipelines.servicestats.service_stats_pipeline.ServiceStatsPipeline',
    #     'schedule': crontab(hour=2, minute=10),
    #     'kwargs': {'product_id': 'highwire_sites'},
    # },
    'get-uptime-every-morning-at-4am': {
        'task': 'ivetl.pipelines.siteuptime.site_uptime_pipeline.SiteUptimePipeline',
        'schedule': crontab(hour=4, minute=0),
        'kwargs': {'product_id': 'highwire_sites', 'run_daily_uptime_alerts': False},
    },
    'run-weekly-uptime-alerts': {
        'task': 'ivetl.pipelines.siteuptime.weekly_alerts_pipeline.WeeklyAlertsPipeline',
        'schedule': crontab(day_of_week=1, hour=7, minute=0),
        'kwargs': {'product_id': 'highwire_sites'},
    },
    # 'monthly-social-metrics': {
    #     'task': 'ivetl.pipelines.socialmetrics.social_metrics_pipeline.SocialMetricsPipeline',
    #     'schedule': crontab(day_of_month=1, hour=0, minute=1),
    #     'kwargs': {'product_id': 'published_articles'},
    # },
    # 'monthly-published-articles-and-article-citations': {
    #     'task': 'ivetl.pipelines.publishedarticles.update_published_articles_pipeline.UpdatePublishedArticlesPipeline',
    #     'schedule': crontab(day_of_month=1, hour=2, minute=0),
    #     'kwargs': {'product_id': 'published_articles', 'run_monthly_job': True},
    # },
    # 'monthly-cohort-articles-and-article-citations': {
    #     'task': 'ivetl.pipelines.publishedarticles.update_published_articles_pipeline.UpdatePublishedArticlesPipeline',
    #     'schedule': crontab(day_of_month=5, hour=2, minute=0),
    #     'kwargs': {'product_id': 'cohort_articles', 'run_monthly_job': True},
    # },
    'monthly-subscription-data': {
        'task': 'ivetl.pipelines.subscriberdata.subscriber_data_pipeline.SubscribersAndSubscriptionsPipeline',
        'schedule': crontab(day_of_month=1, hour=1, minute=0),
        'kwargs': {'product_id': 'institutions'},
    },
    # 'q1-benchpress-rejected-articles': {
    #     'task': 'ivetl.pipelines.rejectedarticles.get_rejected_articles_from_benchpress_pipeline.GetRejectedArticlesFromBenchPressPipeline',
    #     'schedule': crontab(month_of_year=4, day_of_month=1, hour=1, minute=10),
    #     'kwargs': {'product_id': 'rejected_manuscripts'},
    # },
    # 'q2-benchpress-rejected-articles': {
    #     'task': 'ivetl.pipelines.rejectedarticles.get_rejected_articles_from_benchpress_pipeline.GetRejectedArticlesFromBenchPressPipeline',
    #     'schedule': crontab(month_of_year=7, day_of_month=1, hour=1, minute=10),
    #     'kwargs': {'product_id': 'rejected_manuscripts'},
    # },
    # 'q3-benchpress-rejected-articles': {
    #     'task': 'ivetl.pipelines.rejectedarticles.get_rejected_articles_from_benchpress_pipeline.GetRejectedArticlesFromBenchPressPipeline',
    #     'schedule': crontab(month_of_year=10, day_of_month=1, hour=1, minute=10),
    #     'kwargs': {'product_id': 'rejected_manuscripts'},
    # },
    # 'q4-benchpress-rejected-articles': {
    #     'task': 'ivetl.pipelines.rejectedarticles.get_rejected_articles_from_benchpress_pipeline.GetRejectedArticlesFromBenchPressPipeline',
    #     'schedule': crontab(month_of_year=1, day_of_month=1, hour=1, minute=10),
    #     'kwargs': {'product_id': 'rejected_manuscripts'},
    # },
}

CELERY_TIMEZONE = 'US/Pacific'
