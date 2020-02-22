import sys
import os
from getopt import getopt
import traceback
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    filename=os.path.join( os.environ.get('IVWEB_LOG_ROOT', '/var/log/ivweb/'), 'tableau-connector-manual.log'),
    filemode='a',
)

os.sys.path.append(os.environ['IVETL_ROOT'])

from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.common import common
from ivetl.connectors import TableauConnector
from ivetl.models import TableauAlert
from ivetl.tableau_alerts import ALERT_TEMPLATES, ALERT_TEMPLATES_BY_SOURCE_PIPELINE, process_alert

# test code uses django template loader, below mocks out basics for it to run
# https://stackoverflow.com/questions/48163641/django-core-exceptions-appregistrynotready-apps-arent-loaded-yet-django-2-0
# https://stackoverflow.com/questions/98135/how-do-i-use-django-templates-without-the-rest-of-django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ivweb.settings.local")
# from django.conf import settings
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

opts, args = getopt(sys.argv[1:], 'ha:e:mp:', [
    'help',
    'alert-id',
    'email',
    'message-override',
    'publisher'])

publisher_id = None
alert_id = None
email = None
message_override = ('This email was sent as a test. '
    'It likely contains development data. '
    'If you received this email in error, please disregard. '
    'You may contact vizor-support@highwire.org if you questions or concerns. ')

helptext = '''usage: python test_alert.py -- [ -h -e email_address -m ] -a alert_id -p publisher_id

Note: This script will write entries into the provided Cassandra cluster for the
following models:

TableauNotification
TableauNotificationByAlert

Use care to not send an unexpected email to a publisher by mistake, but
either
a) providing an alert id not associated with a publisher email
or
b) providing an email override with the -e option

In case of accidental delivery to the wrong party, this script will override
the custom message with a note that the email is being sent as a test and
should be disregarded. You can override this option (to ensure the saved custom message is included)
by using the -m flag.

Environment variables:

This script uses the open_cassandra_connection and close_cassandra_connection
routines defined in celery.py, which in turn use variables defined in common.py.
The Cassandra IP list can be set with the following variable, e.g:

export IVETL_CASSANDRA_IP=bk-vizor-dev-01.highwire.org

Use a comma separated list for multiple hosts.

This script also connects to a Tableau Server instance.
Set the Tableau instance with the following environment variables:

export IVETL_TABLEAU_SERVER=bk-vizor-win-dev-01.highwire.org
export IVETL_TABLEAU_USERNAME=<user>
export IVETL_TABLEAU_PASSWORD=<password>

e.g. for dev or

export IVETL_TABLEAU_SERVER=reports-data.vizors.org

for the production instance running 2019.4+.

The username you provide (e.g. monitor) will need privileges to view and
export the views required by the alert over the Tableau REST API.

Options and arguments:
-h     :  print this help message and exit (also --help)
-a     :  alert_id. Used to pull record from TableauAlert table in Cassandra. required.
-e     :  email override. optional.
-p     :  publisher_id value to use when querying cassandra. required.
'''

for opt in opts:
    if opt[0] == '-h':
        print(helptext)
        sys.exit()
    if opt[0] == '-a':
        alert_id = opt[1]
    if opt[0] == '-p':
        publisher_id = opt[1]
    if opt[0] == '-e':
        email = opt[1]
        email_override = [email]
    if opt[0] == '-m':
        message_override = None

if not publisher_id:
    print('-p: publisher id required')
    sys.exit()

if not alert_id:
    print('-a: alert_id is required')
    sys.exit()

# testing  tableau_alerts.process_alert(alert, monthly_message=None,
#     attachment_only_emails_override=None, full_emails_override=None,
#     custom_message_override=None):

open_cassandra_connection()


alert = TableauAlert.objects.get(publisher_id=publisher_id, alert_id=alert_id)

process_alert(alert, attachment_only_emails_override=email_override,
    full_emails_override=email_override, custom_message_override=message_override)

close_cassandra_connection()
