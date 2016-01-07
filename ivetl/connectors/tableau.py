import os
import untangle
import requests
import subprocess
import codecs
import time
import datetime
from requests.packages.urllib3.fields import RequestField
from requests.packages.urllib3.filepost import encode_multipart_formdata
from ivetl.common import common
from ivetl.connectors.base import BaseConnector, AuthorizationAPIError


TEMPLATE_PUBLISHER_ID_TO_REPLACE = 'blood'
TEMPLATE_SERVER_TO_REPLACE = 'vizors.stackly.org'

DATA_SOURCES = [
    {
        'id': 'rejected_articles',
        'template_name': 'rejected_articles_ds',
    },
    {
        'id': 'article_citations',
        'template_name': 'article_citations_ds',
    },
    {
        'id': 'article_usage',
        'template_name': 'article_usage_ds',
    },
]
DATA_SOURCES_BY_ID = {d['id']: d for d in DATA_SOURCES}

WORKBOOKS = [
    {
        'id': 'rejected_article_tracker_workbook',
        'name': 'Rejected Article Tracker',
        'template_name': 'rejected_article_tracker',
        'data_source': [DATA_SOURCES_BY_ID['rejected_articles']],
    },
    {
        'id': 'section_performance_analyzer_workbook',
        'name': 'Section Performance Analyzer',
        'template_name': 'section_performance_analyzer',
        'data_source': [DATA_SOURCES_BY_ID['article_citations']],
    },
    {
        'id': 'hot_article_tracker_workbook',
        'name': 'Hot Article Tracker',
        'template_name': 'hot_article_tracker',
        'data_source': [DATA_SOURCES_BY_ID['article_citations'], DATA_SOURCES_BY_ID['article_usage']],
    },
    {
        'id': 'hot_object_tracker_workbook',
        'name': 'Hot Object Tracker',
        'template_name': 'hot_object_tracker',
        'data_source': [DATA_SOURCES_BY_ID['article_citations'], DATA_SOURCES_BY_ID['article_usage']],
    },
    {
        'id': 'citation_distribution_surveyor_workbook',
        'name': 'Citation Distribution Surveyor',
        'template_name': 'citation_distribution_surveyor',
        'data_source': [DATA_SOURCES_BY_ID['article_citations']],
    },
    {
        'id': 'advance_correlator_citation_usage',
        'name': 'Advance Correlator of Citations & Usage',
        'template_name': 'advance_correlator_citation_usage',
        'data_source': [DATA_SOURCES_BY_ID['article_citations'], DATA_SOURCES_BY_ID['article_usage']],
    },
    {
        'id': 'cohort_comparator_workbook',
        'name': 'Cohort Comparator',
        'template_name': 'cohort_comparator',
        'data_source': [DATA_SOURCES_BY_ID['article_citations']],
    },
]
WORKBOOKS_BY_ID = {w['id']: w for w in WORKBOOKS}

TABCMD = os.path.join(common.IVETL_ROOT, 'deploy/tabcmd/tabcmd.sh')


class TableauConnector(BaseConnector):

    def __init__(self, username, password, server):
        self.username = username
        self.password = password
        self.server = server
        self.server_url = 'http://' + self.server
        self.token = ''
        self.user_id = ''
        self.site_id = ''
        self.signed_in = False

    def sign_in(self):
        url = self.server_url + "/api/2.0/auth/signin"

        request_string = """
            <tsRequest>
              <credentials name="%s" password="%s" >
                <site contentUrl="" />
              </credentials>
            </tsRequest>
        """

        self.signed_in = False

        try:
            response = requests.post(url, data=request_string % (self.username, self.password))
            response.raise_for_status()

            r = untangle.parse(response.text).tsResponse
            self.token = r.credentials['token']
            self.site_id = r.credentials.site['id']
            self.user_id = r.credentials.user['id']
            self.signed_in = True
        except:
            raise AuthorizationAPIError()

    def _check_authentication(self):
        if not self.signed_in:
            self.sign_in()

    def create_project(self, project_name):
        self._check_authentication()
        url = self.server_url + "/api/2.0/sites/%s/projects" % self.site_id

        request_string = """
            <tsRequest>
              <project name="%s" />
            </tsRequest>
        """

        response = requests.post(url, data=request_string % project_name, headers={'X-Tableau-Auth': self.token})
        response.raise_for_status()

        r = untangle.parse(response.text).tsResponse
        project_id = r.project['id']
        return project_id

    def create_group(self, group_name):
        self._check_authentication()
        url = self.server_url + "/api/2.0/sites/%s/groups" % self.site_id

        request_string = """
            <tsRequest>
              <group name="%s" />
            </tsRequest>
        """

        response = requests.post(url, data=request_string % group_name, headers={'X-Tableau-Auth': self.token})
        response.raise_for_status()

        r = untangle.parse(response.text).tsResponse
        group_id = r.group['id']

        return group_id

    def add_group_to_project(self, group_id, project_id):
        self._check_authentication()
        url = self.server_url + "/api/2.0/sites/%s/projects/%s/permissions" % (self.site_id, project_id)

        request_string = """
            <tsRequest>
                <permissions>
                    <project id="%s" />
                    <granteeCapabilities>
                        <group id="%s" />
                        <capabilities>
                            <capability name="Connect" mode="Allow" />
                            <capability name="Read" mode="Allow" />
                            <capability name="Filter" mode="Allow" />
                            <capability name="ViewUnderlyingData" mode="Allow" />
                            <capability name="ExportData" mode="Allow" />
                            <capability name="ExportImage" mode="Allow" />
                            <capability name="ViewComments" mode="Deny" />
                            <capability name="AddComment" mode="Deny" />
                            <capability name="WebAuthoring" mode="Deny" />
                            <capability name="ShareView" mode="Deny" />
                        </capabilities>
                    </granteeCapabilities>
                </permissions>
            </tsRequest>
        """

        response = requests.put(url, data=request_string % (project_id, group_id), headers={'X-Tableau-Auth': self.token})
        response.raise_for_status()

    def create_user(self, username):
        self._check_authentication()
        url = self.server_url + "/api/2.0/sites/%s/users" % self.site_id

        request_string = """
            <tsRequest>
                <user name="%s" siteRole="Interactor" />
            </tsRequest>
        """

        response = requests.post(url, data=request_string % username, headers={'X-Tableau-Auth': self.token})
        response.raise_for_status()

        r = untangle.parse(response.text).tsResponse
        user_id = r.user['id']

        return user_id

    def set_user_password(self, user_id, password):
        self._check_authentication()
        url = self.server_url + "/api/2.0/sites/%s/users/%s" % (self.site_id, user_id)

        request_string = """
            <tsRequest>
                <user password="%s" />
            </tsRequest>
        """

        response = requests.put(url, data=request_string % password, headers={'X-Tableau-Auth': self.token})
        response.raise_for_status()

    def add_user_to_group(self, user_id, group_id):
        self._check_authentication()
        url = self.server_url + "/api/2.0/sites/%s/groups/%s/users/" % (self.site_id, group_id)

        request_string = """
            <tsRequest>
                <user id="%s" />
            </tsRequest>
        """

        response = requests.post(url, data=request_string % user_id, headers={'X-Tableau-Auth': self.token})
        response.raise_for_status()

    def list_account_things(self):
        self._check_authentication()

        url = self.server_url + "/api/2.0/sites/%s/projects/" % self.site_id
        response = requests.get(url, headers={'X-Tableau-Auth': self.token})
        print(response.text)

        url = self.server_url + "/api/2.0/sites/%s/groups/" % self.site_id
        response = requests.get(url, headers={'X-Tableau-Auth': self.token})
        print(response.text)

        url = self.server_url + "/api/2.0/sites/%s/users/" % self.site_id
        response = requests.get(url, headers={'X-Tableau-Auth': self.token})
        print(response.text)

    def _make_multipart(self, parts):
        mime_multipart_parts = []

        for name, (filename, blob, content_type) in parts.items():
            multipart_part = RequestField(name=name, data=blob, filename=filename)
            multipart_part.make_multipart(content_type=content_type)
            mime_multipart_parts.append(multipart_part)

        post_body, content_type = encode_multipart_formdata(mime_multipart_parts)
        content_type = ''.join(
            ('multipart/mixed',) + content_type.partition(';')[1:])

        return post_body, content_type

    def add_data_source_to_project(self, project_id, publisher_id, data_source_id, job_id=None):
        self._check_authentication()
        url = self.server_url + "/api/2.0/sites/%s/datasources/?overwrite=true" % self.site_id

        request_string = """
            <tsRequest>
                <datasource name="%s">
                    <project id="%s" />
                </datasource>
            </tsRequest>
        """

        data_source = DATA_SOURCES_BY_ID[data_source_id]

        with codecs.open(os.path.join(common.IVETL_ROOT, 'ivreports/datasources/' + data_source['template_name'] + '.tds'), encoding='utf-8') as f:
            template = f.read()

        data_source_name = data_source['template_name'] + '_' + publisher_id

        if job_id:
            data_source_name += '_' + job_id

        prepared_data_source = template.replace(data_source['template_name'], data_source_name)
        prepared_data_source = prepared_data_source.replace('&apos;%s&apos;' % TEMPLATE_PUBLISHER_ID_TO_REPLACE, '&apos;%s&apos;' % publisher_id)

        with codecs.open(common.TMP_DIR + '/' + data_source_name + '.tds', "w", encoding="utf-8") as fh:
            fh.write(prepared_data_source)

        with codecs.open(common.TMP_DIR + '/' + data_source_name + '.tds', "rb", encoding="utf-8") as fh:
            prepared_data_source_binary = fh.read()

        payload, content_type = self._make_multipart({
            'request_payload': ('', request_string % (data_source_name, project_id), 'text/xml'),
            'tableau_datasource': (data_source_name + '.tds', prepared_data_source_binary, 'application/octet-stream'),
        })

        requests.post(url, data=payload, headers={'X-Tableau-Auth': self.token, 'content-type': content_type})

    def add_workbook_to_project(self, project_id, publisher_id, workbook_id):
        self._check_authentication()
        url = self.server_url + "/api/2.0/sites/%s/workbooks/?overwrite=true&workbookType=twb" % self.site_id

        request_string = """
            <tsRequest>
                <workbook name="%s" showTabs="true">
                    <project id="%s" />
                </workbook>
            </tsRequest>
        """

        workbook = WORKBOOKS_BY_ID[workbook_id]
        with codecs.open(os.path.join(common.IVETL_ROOT, 'ivreports/workbooks/' + workbook['template_name'] + '.twb'), encoding='utf-8') as f:
            template = f.read()

        for ds in workbook['data_source']:
            prepared_workbook = template.replace(ds['template_name'], ds['template_name'] + '_' + publisher_id)

        prepared_workbook = prepared_workbook.replace(TEMPLATE_SERVER_TO_REPLACE, self.server)

        with codecs.open(common.TMP_DIR + '/' + workbook['template_name'] + '_' + publisher_id + '.twb', "w", encoding="utf-8") as fh:
            fh.write(prepared_workbook)

        with codecs.open(common.TMP_DIR + '/' + workbook['template_name'] + '_' + publisher_id + '.twb', "rb", encoding="utf-8") as fh:
            prepared_workbook_binary = fh.read()

        payload, content_type = self._make_multipart({
            'request_payload': ('', request_string % (workbook['name'], project_id), 'text/xml'),
            'tableau_workbook': (workbook['template_name'] + '_' + publisher_id + '.twb', prepared_workbook_binary, 'application/octet-stream'),
        })

        requests.post(url, data=payload, headers={'X-Tableau-Auth': self.token, 'content-type': content_type})

    def setup_account(self, publisher_id, username, password, project_name):

        # create project, group, user, and assign permissions
        project_id = self.create_project(project_name)
        group_id = self.create_group(project_name + " User Group")
        self.add_group_to_project(group_id, project_id)
        user_id = self.create_user(username)
        self.set_user_password(user_id, password)
        self.add_user_to_group(user_id, group_id)

        # add all data sources
        for data_source in DATA_SOURCES:
            fake_job_id = datetime.datetime.now().strftime('%Y%m%d_%H%M%S%f')
            self.add_data_source_to_project(project_id, publisher_id, data_source['id'])
            self.refresh_data_source(publisher_id, project_name, data_source['id'])
            self.add_data_source_to_project(project_id, publisher_id, data_source['id'], job_id=fake_job_id)

        time.sleep(10)

        # and all workbooks, regardless of the selected products
        for workbook in WORKBOOKS:
            self.add_workbook_to_project(project_id, publisher_id, workbook['id'])

        return project_id, group_id, user_id

    def refresh_data_source(self, publisher_id, project_name, data_source_id):
        data_source = DATA_SOURCES_BY_ID[data_source_id]
        data_source_name = data_source['template_name'] + '_' + publisher_id
        login_params = ['-s', self.server, '-u', self.username, '-p', self.password]
        subprocess.call([TABCMD, 'refreshextracts', '--datasource', data_source_name, '--project', project_name] + login_params)
