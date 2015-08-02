from __future__ import absolute_import
import datetime
import sendgrid


ns = {'dc': 'http://purl.org/dc/elements/1.1/',
      'rsp': 'http://schema.highwire.org/Service/Response',
      'nlm': 'http://schema.highwire.org/NLM/Journal',
      'msg': 'http://schema.highwire.org/Service/Message',
      'c': 'http://schema.highwire.org/Compound',
      'x': 'http://www.w3.org/1999/xhtml',
      'xs': 'http://www.w3.org/2001/XMLSchema',
      'e': 'http://schema.highwire.org/Service/HPP/Expand',
      'idx': 'http://schema.highwire.org/Service/Index',
      'atom': 'http://www.w3.org/2005/Atom',
      'frz': 'http://schema.highwire.org/Service/Firenze',
      'xhtml': 'http://www.w3.org/1999/xhtml',
      'opensearch': 'http://a9.com/-/spec/opensearch/1.1',
      'hpp': 'http://schema.highwire.org/Publishing',
      'app': 'http://www.w3.org/2007/app',
      'fs': 'http://sassfs.highwire.org/Service/Content',
      'l': 'http://schema.highwire.org/Linking',
      'cache': 'http://sassfs.highwire.org/Service/Cache',
      'r': 'http://schema.highwire.org/Revision',
      'req': 'http://schema.highwire.org/Service/Request',
      'hwp': 'http://schema.highwire.org/Journal',
      'xref': 'http://www.crossref.org/qrschema/2.0',
      'results': 'http://schema.highwire.org/SQL/results'}

sass_url = "http://sass.highwire.org"

CASSANDRA_IP = '10.0.1.12'
CASSANDRA_KEYSPACE_IV = 'impactvizor'

BASE_INCOMING_DIR = "/iv/incoming/"
BASE_WORK_DIR = "/iv/working/"
BASE_ARCHIVE_DIR = "/iv/archive/"

RAT = "rejected_article_tracker"

PA = "published_articles"
PA_PUB_START_DATE = datetime.date(2010, 1, 1)
PA_PUB_OVERLAP_MONTHS = 2

AC = "article_citations"

EMAIL = "nmehta@highwire.org"
FROM = "impactvizor@highwire.org"
SG_USERNAME = "estacks"
SG_PWD = "Hello123!"


def sendEmail(subject, body):

        try:
            sg = sendgrid.SendGridClient(SG_USERNAME, SG_PWD)

            message = sendgrid.Mail()
            message.add_to(EMAIL)
            message.set_subject(subject)
            message.set_html(body)
            message.set_from(FROM)

            sg.send(message)

        except Exception:
            # do nothing
            print("sending of email failed")



