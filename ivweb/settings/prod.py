from ivweb.settings.base import *

LOCAL = False
DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = False

DATABASES = {
    'default': {
        'ENGINE': 'django_cassandra_engine',
        'NAME': 'impactvizor',
        'HOST': '127.0.0.1',
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
