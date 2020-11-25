from ivweb.settings.base import *
from ivetl.common import common

LOCAL = True
DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = True

DATABASES = {
    'default': {
        'ENGINE': 'django_cassandra_engine',
        'NAME': common.CASSANDRA_KEYSPACE_IV,
        'HOST': ",".join(common.CASSANDRA_IP_LIST),
        'OPTIONS': {
            'replication': {
                'strategy_class': 'SimpleStrategy',
                'replication_factor': 1,
            },
            'connection': {
                'lazy_connect': True,
                'retry_connect': True,
                'consistency': 1,
                'connect_timeout': 60,
                'control_connection_timeout': 60
            },
            'session': {
                'default_timeout': 60
            }
        }
    }
}

SECURE_SSL_REDIRECT = False
