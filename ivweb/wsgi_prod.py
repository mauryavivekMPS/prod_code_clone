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
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ivweb.settings.prod")

os.environ["IVETL_ROOT"] = "/iv/impactvizor-pipeline"
os.environ["IVETL_TABLEAU_SERVER"] = "reports-data.vizors.org"
os.environ["IVETL_TABLEAU_IP"] = "10.0.1.44"
os.environ["IVETL_TABLEAU_HTTPS"] = "1"
os.environ["IVETL_TABLEAU_USERNAME"] = "monitor"
os.environ["IVETL_TABLEAU_PASSWORD"] = "M5NbtYmT"
os.environ["IVETL_CASSANDRA_IP"] = "10.0.1.93,10.0.1.116,10.0.1.248"
os.environ["IVETL_WEB_ADDRESS"] = "https://manage.vizors.org"
os.environ["IVETL_RABBITMQ_BROKER_URL"] = "amqp://guest:guest@10.0.1.174:5672//;amqp://guest:guest@10.0.1.185:5672//"
os.environ["IVETL_RATE_LIMITER_SERVER"] = "10.0.1.174:8082"

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Apply WSGI middleware here.
# from helloworld.wsgi import HelloWorldApplication
# application = HelloWorldApplication(application)
