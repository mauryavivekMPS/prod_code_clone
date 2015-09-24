import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

IVETL_ROOT = os.environ['IVETL_ROOT']

DEBUG = False

APP_NAME = 'Impact Vizor Admin'

ADMINS = (
    ('IVETL Admin', 'admin@ivetl.admin'),
)

MANAGERS = ADMINS

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'US/Pacific'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = '/var/ivetl/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
# ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    # 'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '%%u-6vvmop1@cxqetfbyeasdff7g8^k7v#xyb0z+c$6(a7zb0jk6h'

TEMPLATES = [
    {
        'NAME': 'django',
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(IVETL_ROOT, "ivweb/app/templates"),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': (
                "django.contrib.auth.context_processors.auth",
                "django.core.context_processors.request",
                "django.contrib.messages.context_processors.messages",
            ),
            'debug': False,
        },
    },
]

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'ivweb.app.middleware.account_resolver.AccountResolverMiddleware',
    # 'ivweb.app.middleware.recent_account.RecentAccountMiddleware',
    'easy_pjax.middleware.UnpjaxMiddleware',
)

ROOT_URLCONF = 'ivweb.urls'

INSTALLED_APPS = (
    'django_cassandra_engine',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'easy_pjax',
    'ivweb.app',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

LOGIN_URL = "/login/"
LOGOUT_URL = "/logout/"

LOG_ROOT = os.environ.get('IVWEB_LOG_ROOT', '/var/log/ivweb')
ENABLE_CACHE_LOGGING = False

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_ROOT, 'app.log'),
            'formatter': 'verbose'
        },
        'tools_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_ROOT, 'tools.log'),
            'formatter': 'verbose'
        },
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },

    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'ivweb': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
        'simplecache': {
            'handlers': ['file'],
            # 'level': 'WARNING',  # change to DEBUG to see all the cache activity
            'level': 'DEBUG',
        },
        'django.db.backends': {
            'handlers': ['null'],
            'propagate': False,
            'level': 'DEBUG',
        },
    }
}
