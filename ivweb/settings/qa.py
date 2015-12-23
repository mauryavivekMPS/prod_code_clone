from ivweb.settings.base import *

LOCAL = False
DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = True

DATABASES = {
    'default': {
        'ENGINE': 'django_cassandra_engine',
        'NAME': 'impactvizor',
        'HOST': '10.0.0.115',
    }
}

SECURE_SSL_REDIRECT = False
