import os
import untangle
import requests
from requests.packages.urllib3.fields import RequestField
from requests.packages.urllib3.filepost import encode_multipart_formdata
from ivetl.models import Publisher_Metadata
from ivetl.common import common

TEMPLATE_PUBLISHER_ID = 'blood'

DATA_SOURCES = [
    {
        'id': 'rejected_articles',
        'template_name': 'rejected_articles_ds',
        'extension': '.tds',
    },
    {
        'id': 'article_citations',
        'template_name': 'article_citations_ds',
        'extension': '.tds',
    },
]
DATA_SOURCES_BY_ID = {d['id']: d for d in DATA_SOURCES}

WORKBOOKS = [
    {
        'id': 'rejected_article_tracker',
        'name': 'Rejected Article Tracker',
        'template_name': 'rejected_article_tracker',
        'data_source': DATA_SOURCES_BY_ID['rejected_articles'],
    },
    {
        'id': 'section_performance_analyzer',
        'name': 'Section Performance Analyzer',
        'template_name': 'section_performance_analyzer',
        'data_source': DATA_SOURCES_BY_ID['article_citations'],
    },
    {
        'id': 'hot_article_tracker',
        'name': 'Hot Article Tracker',
        'template_name': 'hot_article_tracker',
        'data_source': DATA_SOURCES_BY_ID['article_citations'],
    },
    {
        'id': 'hot_object_tracker',
        'name': 'Hot Object Tracker',
        'template_name': 'hot_object_tracker',
        'data_source': DATA_SOURCES_BY_ID['article_citations'],
    },
    {
        'id': 'citation_distribution_surveyor',
        'name': 'Citation Distribution Surveyor',
        'template_name': 'citation_distribution_surveyor',
        'data_source': DATA_SOURCES_BY_ID['article_citations'],
    },
    {
        'id': 'cohort_comparator',
        'name': 'Cohort Comparator',
        'template_name': 'cohort_comparator',
        'data_source': DATA_SOURCES_BY_ID['article_citations'],
    },
]


class TableauClient(object):

    def __init__(self, username='admin', password='admin', server='http://10.0.0.143'):
        self.username = username
        self.password = password
        self.server = server
        self.token = ''
        self.user_id = ''
        self.site_id = ''

    def sign_in(self):
        url = self.server + "/api/2.0/auth/signin"

        request_string = """
            <tsRequest>
              <credentials name="%s" password="%s" >
                <site contentUrl="" />
              </credentials>
            </tsRequest>
        """

        response = requests.post(url, data=request_string % (self.username, self.password))
        if response.status_code != 200:
            print('There was an error:')
            print(response.text)

        r = untangle.parse(response.text).tsResponse
        self.token = r.credentials['token']
        self.site_id = r.credentials.site['id']
        self.user_id = r.credentials.user['id']

        print('The token is: %s' % self.token)

    def create_project(self, project_name):
        url = self.server + "/api/2.0/sites/%s/projects" % self.site_id

        request_string = """
            <tsRequest>
              <project name="%s" />
            </tsRequest>
        """

        response = requests.post(url, data=request_string % project_name, headers={'X-Tableau-Auth': self.token})
        if response.status_code != 201:
            print('There was an error:')
            print(response.text)

        r = untangle.parse(response.text).tsResponse
        project_id = r.project['id']
        print('The new project ID is: %s' % project_id)
        return project_id

    def create_group(self, group_name):
        url = self.server + "/api/2.0/sites/%s/groups" % self.site_id

        request_string = """
            <tsRequest>
              <group name="%s" />
            </tsRequest>
        """

        response = requests.post(url, data=request_string % group_name, headers={'X-Tableau-Auth': self.token})
        if response.status_code != 201:
            print('There was an error:')
            print(response.text)

        r = untangle.parse(response.text).tsResponse
        group_id = r.group['id']

        print('The new group ID is: %s' % group_id)
        return group_id

    def add_group_to_project(self, group_id, project_id):
        url = self.server + "/api/2.0/sites/%s/projects/%s/permissions" % (self.site_id, project_id)

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
        if response.status_code != 200:
            print('There was an error:')
            print(response.text)

    def create_user(self, username):
        url = self.server + "/api/2.0/sites/%s/users" % self.site_id

        request_string = """
            <tsRequest>
                <user name="%s" siteRole="Interactor" />
            </tsRequest>
        """

        response = requests.post(url, data=request_string % username, headers={'X-Tableau-Auth': self.token})
        if response.status_code != 201:
            print('There was an error:')
            print(response.text)

        r = untangle.parse(response.text).tsResponse
        user_id = r.user['id']

        print('The new user ID is: %s' % user_id)
        return user_id

    def set_user_password(self, user_id, password):
        url = self.server + "/api/2.0/sites/%s/users/%s" % (self.site_id, user_id)

        request_string = """
            <tsRequest>
                <user password="%s" />
            </tsRequest>
        """

        response = requests.put(url, data=request_string % password, headers={'X-Tableau-Auth': self.token})
        if response.status_code != 200:
            print('There was an error:')
            print(response.text)

    def add_user_to_group(self, user_id, group_id):
        url = self.server + "/api/2.0/sites/%s/groups/%s/users/" % (self.site_id, group_id)

        request_string = """
            <tsRequest>
                <user id="%s" />
            </tsRequest>
        """

        response = requests.post(url, data=request_string % user_id, headers={'X-Tableau-Auth': self.token})
        if response.status_code != 200:
            print('There was an error:')
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

    def add_data_sources_to_project(self, project_id, publisher_id):
        url = self.server + "/api/2.0/sites/%s/datasources/?overwrite=true" % self.site_id

        request_string = """
            <tsRequest>
                <datasource name="%s">
                    <project id="%s" />
                </datasource>
            </tsRequest>
        """

        for data_source in DATA_SOURCES:
            with open(os.path.join(common.IVETL_ROOT, 'ivreports/datasources/' + data_source['template_name'] + '.tds'), 'rt') as f:
                template = f.read()

            data_source_name = data_source['template_name'] + '_' + publisher_id

            prepared_data_source = template.replace(data_source['template_name'], data_source_name)
            prepared_data_source = prepared_data_source.replace('&apos;%s&apos;' % TEMPLATE_PUBLISHER_ID, '&apos;%s&apos;' % publisher_id)

            payload, content_type = self._make_multipart({
                'request_payload': ('', request_string % (data_source_name, project_id), 'text/xml'),
                'tableau_datasource': (data_source_name + '.tds', prepared_data_source, 'application/octet-stream'),
            })

            requests.post(url, data=payload, headers={'X-Tableau-Auth': self.token, 'content-type': content_type})

    def add_workbooks_to_project(self, project_id, publisher_id):
        url = self.server + "/api/2.0/sites/%s/workbooks/?overwrite=true&workbookType=twb" % self.site_id

        request_string = """
            <tsRequest>
                <workbook name="%s" showTabs="true">
                    <project id="%s" />
                </workbook>
            </tsRequest>
        """

        for workbook in WORKBOOKS:
            with open(os.path.join(common.IVETL_ROOT, 'ivreports/workbooks/' + workbook['template_name'] + '.twb'), 'rt') as f:
                template = f.read()

            prepared_workbook = template.replace(workbook['data_source']['template_name'],  workbook['data_source']['template_name'] + '_' + publisher_id)

            with open('/Users/john/Desktop/' + workbook['template_name'] + '_' + publisher_id + '.twb', 'wt') as f:
                f.write(prepared_workbook)

            payload, content_type = self._make_multipart({
                'request_payload': ('', request_string % (workbook['name'], project_id), 'text/xml'),
                'tableau_workbook': (workbook['template_name'] + '_' + publisher_id + '.twb', prepared_workbook, 'application/octet-stream'),
            })

            response = requests.post(url, data=payload, headers={'X-Tableau-Auth': self.token, 'content-type': content_type})

            print(response.status_code)
            print(response.text)

    def setup_account(self, publisher_id, project_name, username, password):
        publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)

        self.sign_in()
        project_id = self.create_project(project_name)
        group_id = self.create_group(project_name)
        self.add_group_to_project(group_id, project_id)
        user_id = self.create_user(username)
        self.set_user_password(user_id, password)
        self.add_user_to_group(user_id, group_id)

        # save ID for later
        publisher.reports_project_id = project_id
        publisher.reports_group_id = group_id
        publisher.reports_user_id = user_id
        publisher.save()
