from ivweb.settings.base import *
from ivetl.common import common

LOCAL = True
DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = True

DATABASES = {
    'default': {
        'ENGINE': 'django_cassandra_engine',
        'NAME': common.CASSANDRA_KEYSPACE_IV,
        'HOST': common.CASSANDRA_IP,
        'OPTIONS': {
            'replication': {
                'strategy_class': 'SimpleStrategy',
                'replication_factor': 1,
            },
            'connection': {
                'lazy_connect': True,
                'retry_connect': True,
                'consistency': 1
            },
            'session': {
                'default_timeout': 15
            }
        }
    }
}

SECURE_SSL_REDIRECT = False
