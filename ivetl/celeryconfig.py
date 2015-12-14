import os
from ivetl.common import common

BROKER_URL = 'amqp://guest:guest@' + common.RABBITMQ_BROKER_IP + ':5672//'

CELERY_IMPORTS = (
    'ivetl.pipelines.publishedarticles',
    'ivetl.pipelines.customarticledata',
    'ivetl.pipelines.articlecitations',
    'ivetl.pipelines.rejectedarticles',
    'ivetl.pipelines.articleusage',
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
