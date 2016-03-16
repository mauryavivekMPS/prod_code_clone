import os
from celery.schedules import crontab
from ivetl.common import common

BROKER_URL = 'amqp://guest:guest@' + common.RABBITMQ_BROKER_IP + ':5672//'

CELERY_IMPORTS = (
    'ivetl.pipelines.publishedarticles',
    'ivetl.pipelines.customarticledata',
    'ivetl.pipelines.articlecitations',
    'ivetl.pipelines.rejectedarticles',
    'ivetl.pipelines.articleusage',
    'ivetl.pipelines.sitemetadata',
    'ivetl.pipelines.siteuptime',
    'ivetl.tasks',
)

CELERY_TASK_RESULT_EXPIRES = 3600
CELERY_ACKS_LATE = False
CELERYD_PREFETCH_MULTIPLIER = 1
CELERY_TRACK_STARTED = False
CELERY_SEND_TASK_ERROR_EMAILS = True

# Name and email addresses of recipients
ADMINS = (
    ('IVETL Admin', os.environ.get('IVETL_EMAIL_TO_ADDRESS', "nmehta@highwire.org")),
)

# Email address used as sender (From field).
SERVER_EMAIL = 'impactvizor@highwire.org'

# Mailserver configuration
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'estacks'
EMAIL_HOST_PASSWORD = 'Hello123!'

CELERYBEAT_SCHEDULE = {
    'get-uptime-every-morning-at-2am': {
        'task': 'ivetl.pipelines.siteuptime.SiteUptimePipeline.SiteUptimePipeline',
        'schedule': crontab(hour=2, minute=0),
        'kwargs': {'publisher_id_list': ['hw'], 'product_id': 'highwire_sites'},
    },
    'monthly-published-articles-and-article-citations': {
        'task': 'ivetl.pipelines.publishedarticles.UpdatePublishedArticlesPipeline.UpdatePublishedArticlesPipeline',
        'schedule': crontab(day_of_month=1, hour=1, minute=0),
        'kwargs': {'product_id': 'published_articles', 'run_monthly_job': True},
    },
    'monthly-cohort-articles-and-article-citations': {
        'task': 'ivetl.pipelines.publishedarticles.UpdatePublishedArticlesPipeline.UpdatePublishedArticlesPipeline',
        'schedule': crontab(day_of_month=1, hour=1, minute=10),
        'kwargs': {'product_id': 'cohort_articles', 'run_monthly_job': True},
    },
}

CELERY_TIMEZONE = 'US/Pacific'
