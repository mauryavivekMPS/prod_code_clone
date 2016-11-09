from ivetl.common import common
from ivweb.settings.base import *

LOCAL = False
DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = False

DATABASES = {
    'default': {
        'ENGINE': 'django_cassandra_engine',
        'NAME': 'impactvizor',
        'HOST': ",".join(common.CASSANDRA_IP_LIST),
    }
}

ALLOWED_HOSTS = [
    '10.0.1.99',
    '10.0.1.19',
    'manage.vizors.org',
    'managenew.vizors.org',
]
