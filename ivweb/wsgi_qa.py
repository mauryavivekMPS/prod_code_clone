"""
WSGI config for ivweb project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""

import os

# We defer to a DJANGO_SETTINGS_MODULE already in the environment. This breaks
# if running multiple sites in the same mod_wsgi process. To fix this, use
# mod_wsgi daemon mode with each site in its own daemon process, or use
# os.environ["DJANGO_SETTINGS_MODULE"] = "bloop.settings"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ivweb.settings.qa")

os.environ["IVETL_ROOT"] = "/iv/impactvizor-pipeline"
# os.environ["IVETL_TABLEAU_SERVER"] = "10.0.0.143"
# os.environ["IVETL_TABLEAU_USERNAME"] = "admin"
# os.environ["IVETL_TABLEAU_PASSWORD"] = "admin"
os.environ["IVETL_CASSANDRA_IP"] = "10.0.0.21"
os.environ["IVETL_EMAIL_TO_ADDRESS"] = "john@lonepixel.com"
os.environ["IVETL_WEB_ADDRESS"] = "http://10.0.0.232"
os.environ["IVETL_RABBITMQ_BROKER_URL"] = "amqp://guest:guest@10.0.1.99:5672//"

# temporarily

os.environ["IVETL_TABLEAU_SERVER"] = "vizors.org"
os.environ["IVETL_TABLEAU_USERNAME"] = "nmehta"
os.environ["IVETL_TABLEAU_PASSWORD"] = "Reena,1275"

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Apply WSGI middleware here.
# from helloworld.wsgi import HelloWorldApplication
# application = HelloWorldApplication(application)
