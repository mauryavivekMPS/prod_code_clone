
CELERY_TASK_RESULT_EXPIRES = 3600

BROKER_URL = 'amqp://guest:guest@localhost:5672//'

#CELERYD_CONCURRENCY = 4

CELERY_ACKS_LATE = False
CELERYD_PREFETCH_MULTIPLIER = 1

CELERY_TRACK_STARTED = False

# Enables error emails.
CELERY_SEND_TASK_ERROR_EMAILS = True

# Name and email addresses of recipients
ADMINS = (
    # ('Neil Mehta', 'nmehta@highwire.org'),
)

# Email address used as sender (From field).
SERVER_EMAIL = 'impactvizor@highwire.org'

# Mailserver configuration
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'estacks'
EMAIL_HOST_PASSWORD = 'Hello123!'




