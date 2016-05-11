from ivetl.common import common
from ivweb.settings.base import *

LOCAL = False
DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = True

DATABASES = {
    'default': {
        'ENGINE': 'django_cassandra_engine',
        'NAME': 'impactvizor',
        'HOST': ",".join(common.CASSANDRA_IP_LIST),
    }
}

SECURE_SSL_REDIRECT = False
