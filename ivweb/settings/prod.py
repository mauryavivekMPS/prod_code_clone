from ivweb.settings.base import *

LOCAL = False
DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = False

DATABASES = {
    'default': {
        'ENGINE': 'django_cassandra_engine',
        'NAME': 'impactvizor',
        'HOST': '10.0.1.12',
    }
}

ALLOWED_HOSTS = ['10.0.1.99']
