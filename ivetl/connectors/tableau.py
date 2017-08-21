import os
import re
import csv
import untangle
import requests
import subprocess
import time
import tempfile
import datetime
from requests.packages.urllib3.fields import RequestField
from requests.packages.urllib3.filepost import encode_multipart_formdata
from ivetl.common import common
from ivetl.connectors.base import BaseConnector, AuthorizationAPIError
from ivetl.models import WorkbookUrl


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
        url = self.server_url + "/api/2.5/auth/signin"

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

    def _tabcmd_login_params(self):
        return ['-s', self.server + ':80', '-u', self.username, '-p', self.password]

    def create_project(self, project_name):
        self._check_authentication()
        url = self.server_url + "/api/2.5/sites/%s/projects" % self.site_id

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
        url = self.server_url + "/api/2.5/sites/%s/groups" % self.site_id

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
        url = self.server_url + "/api/2.5/sites/%s/projects/%s/permissions" % (self.site_id, project_id)

        request_string = """
            <tsRequest>
                <permissions>
                    <project id="%s" />
                    <granteeCapabilities>
                        <group id="%s" />
                        <capabilities>
                            <capability name="Read" mode="Allow" />
                        </capabilities>
                    </granteeCapabilities>
                </permissions>
            </tsRequest>
        """

        response = requests.put(url, data=request_string % (project_id, group_id), headers={'X-Tableau-Auth': self.token})
        response.raise_for_status()

    def add_default_workbook_permissions_for_project(self, group_id, project_id):
        self._check_authentication()
        url = self.server_url + "/api/2.5/sites/%s/projects/%s/default-permissions/workbooks" % (self.site_id, project_id)

        request_string = """
            <tsRequest>
                <permissions>
                    <project id="%s" />
                    <granteeCapabilities>
                        <group id="%s" />
                        <capabilities>
                            <capability name="Read" mode="Allow" />
                            <capability name="Filter" mode="Allow" />
                            <capability name="ExportImage" mode="Allow" />
                            <capability name="ExportData" mode="Allow" />
                        </capabilities>
                    </granteeCapabilities>
                </permissions>
            </tsRequest>
        """

        response = requests.put(url, data=request_string % (project_id, group_id), headers={'X-Tableau-Auth': self.token})
        response.raise_for_status()

    def add_default_datasource_permissions_for_project(self, group_id, project_id):
        self._check_authentication()
        url = self.server_url + "/api/2.5/sites/%s/projects/%s/default-permissions/datasources" % (self.site_id, project_id)

        request_string = """
            <tsRequest>
                <permissions>
                    <project id="%s" />
                    <granteeCapabilities>
                        <group id="%s" />
                        <capabilities>
                            <capability name="Read" mode="Allow" />
                            <capability name="Connect" mode="Allow" />
                        </capabilities>
                    </granteeCapabilities>
                </permissions>
            </tsRequest>
        """

        response = requests.put(url, data=request_string % (project_id, group_id), headers={'X-Tableau-Auth': self.token})
        response.raise_for_status()

    def create_user(self, username):
        self._check_authentication()
        url = self.server_url + "/api/2.5/sites/%s/users" % self.site_id

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
        url = self.server_url + "/api/2.5/sites/%s/users/%s" % (self.site_id, user_id)

        request_string = """
            <tsRequest>
                <user password="%s" />
            </tsRequest>
        """

        response = requests.put(url, data=request_string % password, headers={'X-Tableau-Auth': self.token})
        response.raise_for_status()

    def add_user_to_group(self, user_id, group_id):
        self._check_authentication()
        url = self.server_url + "/api/2.5/sites/%s/groups/%s/users/" % (self.site_id, group_id)

        request_string = """
            <tsRequest>
                <user id="%s" />
            </tsRequest>
        """

        response = requests.post(url, data=request_string % user_id, headers={'X-Tableau-Auth': self.token})
        response.raise_for_status()

    def list_account_things(self):
        self._check_authentication()

        url = self.server_url + "/api/2.5/sites/%s/projects/" % self.site_id
        response = requests.get(url, headers={'X-Tableau-Auth': self.token})
        print(response.text)

        url = self.server_url + "/api/2.5/sites/%s/groups/" % self.site_id
        response = requests.get(url, headers={'X-Tableau-Auth': self.token})
        print(response.text)

        url = self.server_url + "/api/2.5/sites/%s/users/" % self.site_id
        response = requests.get(url, headers={'X-Tableau-Auth': self.token})
        print(response.text)

        url = self.server_url + "/api/2.5/sites/%s/datasources/" % self.site_id
        response = requests.get(url, headers={'X-Tableau-Auth': self.token})
        print(response.text)

        url = self.server_url + "/api/2.5/sites/%s/users/%s/workbooks/" % (self.site_id, self.user_id)
        response = requests.get(url, headers={'X-Tableau-Auth': self.token})
        print(response.text)

    def list_datasources(self, project_id=None):
        self._check_authentication()

        url = self.server_url + "/api/2.5/sites/%s/datasources/" % self.site_id
        response = requests.get(url, params={'pageSize': 1000}, headers={'X-Tableau-Auth': self.token})
        r = untangle.parse(response.text).tsResponse
        all_datasources = [{'name': d['name'], 'id': d['id'], 'project_id': d.project['id']} for d in r.datasources.datasource]

        if project_id:
            filtered_datasources = [d for d in all_datasources if d['project_id'] == project_id]
        else:
            filtered_datasources = all_datasources

        return filtered_datasources

    def list_workbooks(self, project_id=None):
        self._check_authentication()

        url = self.server_url + "/api/2.5/sites/%s/users/%s/workbooks/" % (self.site_id, self.user_id)
        response = requests.get(url, params={'pageSize': 1000}, headers={'X-Tableau-Auth': self.token})
        r = untangle.parse(response.text).tsResponse
        all_workbooks = [{'name': d['name'], 'id': d['id'], 'project_id': d.project['id'], 'url': d['contentUrl']} for d in r.workbooks.workbook]

        if project_id:
            filtered_workbooks = [w for w in all_workbooks if w['project_id'] == project_id]
        else:
            filtered_workbooks = all_workbooks

        return filtered_workbooks

    def _make_multipart(self, parts):
        mime_multipart_parts = []

        for name, (filename, blob, content_type) in parts.items():
            multipart_part = RequestField(name=name, data=blob, filename=filename)
            multipart_part.make_multipart(content_type=content_type)
            mime_multipart_parts.append(multipart_part)

        post_body, content_type = encode_multipart_formdata(mime_multipart_parts)
        content_type = ''.join(('multipart/mixed',) + content_type.partition(';')[1:])

        return post_body, content_type

    def _base_datasource_name(self, datasource_id):
        return datasource_id[:-len(common.TABLEAU_DATASOURCE_FILE_EXTENSION)]

    def _base_workbook_name(self, workbook_id):
        return workbook_id[:-len(common.TABLEAU_WORKBOOK_FILE_EXTENSION)]

    def _publisher_datasource_name(self, publisher, datasource_id):
        return self._base_datasource_name(datasource_id) + '_' + publisher.publisher_id

    def _publisher_workbook_name(self, publisher, workbook_id):
        return self._base_workbook_name(workbook_id) + '_' + publisher.publisher_id

    def _base_datasource_name_from_publisher_name(self, publisher, publisher_datasource_name):
        return publisher_datasource_name[:-(len(publisher.publisher_id) + 1)] + common.TABLEAU_DATASOURCE_FILE_EXTENSION

    def _base_workbook_name_from_publisher_name(self, publisher, publisher_workbook_name):
        return publisher_workbook_name[:-(len(publisher.publisher_id) + 1)] + common.TABLEAU_WORKBOOK_FILE_EXTENSION

    def refresh_data_source(self, publisher, datasource_id):
        datasource_name = self._publisher_datasource_name(publisher, datasource_id)
        subprocess.call([common.TABCMD, 'refreshextracts', '--datasource', datasource_name, '--project', publisher.reports_project] + self._tabcmd_login_params())

    def delete_datasource_from_project(self, tableau_datasource_id):
        self._check_authentication()
        url = self.server_url + "/api/2.5/sites/%s/datasources/%s" % (self.site_id, tableau_datasource_id)
        requests.delete(url, headers={'X-Tableau-Auth': self.token})

    def delete_workbook_from_project(self, tableau_workbook_id):
        self._check_authentication()
        url = self.server_url + "/api/2.5/sites/%s/workbooks/%s" % (self.site_id, tableau_workbook_id)
        requests.delete(url, headers={'X-Tableau-Auth': self.token})

    def add_datasource_to_project(self, publisher, datasource_id):
        self._check_authentication()
        url = self.server_url + "/api/2.5/sites/%s/datasources/?overwrite=true" % self.site_id

        request_string = """
            <tsRequest>
                <datasource name="%s">
                    <project id="%s" />
                </datasource>
            </tsRequest>
        """

        with open(os.path.join(common.IVETL_ROOT, 'ivreports/datasources/' + datasource_id), encoding='utf-8') as f:
            template = f.read()

        base_datasource_name = self._base_datasource_name(datasource_id)
        publisher_datasource_name = self._publisher_datasource_name(publisher, datasource_id)

        prepared_datasource = re.sub('(?<!%s\\\)%s' % (common.TABLEAU_DUMMY_EXTRACTS_DIR_NAME, base_datasource_name), publisher_datasource_name, template)
        prepared_datasource = prepared_datasource.replace('&apos;%s&apos;' % common.TABLEAU_TEMPLATE_PUBLISHER_ID_TO_REPLACE, '&apos;%s&apos;' % publisher.publisher_id)

        with open(os.path.join(common.TMP_DIR, publisher_datasource_name + common.TABLEAU_DATASOURCE_FILE_EXTENSION), "w", encoding="utf-8") as fh:
            fh.write(prepared_datasource)

        with open(os.path.join(common.TMP_DIR, publisher_datasource_name + common.TABLEAU_DATASOURCE_FILE_EXTENSION), "rb") as fh:
            prepared_datasource_binary = fh.read()

        payload, content_type = self._make_multipart({
            'request_payload': ('', request_string % (publisher_datasource_name, publisher.reports_project_id), 'text/xml'),
            'tableau_datasource': (publisher_datasource_name + common.TABLEAU_DATASOURCE_FILE_EXTENSION, prepared_datasource_binary, 'application/octet-stream'),
        })

        response = requests.post(url, data=payload, headers={'X-Tableau-Auth': self.token, 'content-type': content_type})
        response.raise_for_status()

        r = untangle.parse(response.text).tsResponse

        datasource_tableau_id = r.datasource['id']

        return {
            'tableau_id': datasource_tableau_id,
        }

    def add_workbook_to_project(self, publisher, workbook_id):
        self._check_authentication()
        url = self.server_url + "/api/2.5/sites/%s/workbooks/?overwrite=true&workbookType=twb" % self.site_id

        request_string = """
            <tsRequest>
                <workbook name="%s" showTabs="true">
                    <project id="%s" />
                </workbook>
            </tsRequest>
        """

        workbook = common.TABLEAU_WORKBOOKS_BY_ID[workbook_id]
        with open(os.path.join(common.IVETL_ROOT, 'ivreports/workbooks/' + workbook_id), encoding='utf-8') as f:
            prepared_workbook = f.read()

        all_datasources_for_publisher = publisher.all_datasources

        for datasource_id in all_datasources_for_publisher:
            base_datasource_name = self._base_datasource_name(datasource_id)
            publisher_datasource_name = self._publisher_datasource_name(publisher, datasource_id)
            prepared_workbook = prepared_workbook.replace(base_datasource_name, publisher_datasource_name)

        prepared_workbook = prepared_workbook.replace(common.TABLEAU_TEMPLATE_SERVER_TO_REPLACE, self.server)

        publisher_workbook_name = self._publisher_workbook_name(publisher, workbook_id)

        with open(os.path.join(common.TMP_DIR, publisher_workbook_name + common.TABLEAU_WORKBOOK_FILE_EXTENSION), "w", encoding="utf-8") as fh:
            fh.write(prepared_workbook)

        with open(os.path.join(common.TMP_DIR, publisher_workbook_name + common.TABLEAU_WORKBOOK_FILE_EXTENSION), "rb") as fh:
            prepared_workbook_binary = fh.read()

        workbook_name = workbook['name'].replace('&', '&amp;')

        payload, content_type = self._make_multipart({
            'request_payload': ('', request_string % (workbook_name, publisher.reports_project_id), 'text/xml'),
            'tableau_workbook': (publisher_workbook_name + common.TABLEAU_WORKBOOK_FILE_EXTENSION, prepared_workbook_binary, 'application/octet-stream'),
        })

        response = requests.post(url, data=payload, headers={'X-Tableau-Auth': self.token, 'content-type': content_type})
        response.raise_for_status()

        r = untangle.parse(response.text).tsResponse

        workbook_url = r.workbook['contentUrl']
        workbook_tableau_id = r.workbook['id']

        WorkbookUrl.objects(
            publisher_id=publisher.publisher_id,
            workbook_id=workbook_id,
        ).update(
            url=workbook_url
        )

        # remove group permissions if this is an admin_only template
        if workbook.get('admin_only', False):
            self.remove_group_permissions_for_workbook(publisher.reports_group_id, workbook_tableau_id)

        return {
            'url': workbook_url,
            'tableau_id': workbook_tableau_id,
        }

    def remove_group_permissions_for_workbook(self, group_id, workbook_tableau_id):
        self._check_authentication()
        for capability in ['Read', 'Filter', 'ViewUnderlyingData', 'ExportData', 'ExportImage']:
            url = self.server_url + "/api/2.5/sites/%s/workbooks/%s/permissions/groups/%s/%s/Allow" % (
                self.site_id,
                workbook_tableau_id,
                group_id,
                capability
            )
            requests.delete(url, headers={'X-Tableau-Auth': self.token})

    def update_datasources_and_workbooks(self, publisher):
        required_datasource_ids = set()
        for product_group_id in publisher.supported_product_groups:
            for datasource_id in common.PRODUCT_GROUP_BY_ID[product_group_id]['tableau_datasources']:
                required_datasource_ids.add(datasource_id)

        existing_datasources = self.list_datasources(project_id=publisher.reports_project_id)
        existing_datasource_ids = set([self._base_datasource_name_from_publisher_name(publisher, d['name']) for d in existing_datasources])
        datasource_tableau_id_lookup = {self._base_datasource_name_from_publisher_name(publisher, d['name']): d['id'] for d in existing_datasources}

        for datasource_id in existing_datasource_ids - required_datasource_ids:
            self.delete_datasource_from_project(datasource_tableau_id_lookup[datasource_id])

        for datasource_id in required_datasource_ids - existing_datasource_ids:
            self.add_datasource_to_project(publisher, datasource_id)
            self.refresh_data_source(publisher, datasource_id)

        time.sleep(10)

        required_workbook_ids = set()
        for product_group_id in publisher.supported_product_groups:
            for workbook_id in common.PRODUCT_GROUP_BY_ID[product_group_id]['tableau_workbooks']:
                required_workbook_ids.add(workbook_id)

        workbook_id_lookup = {w['name']: w['id'] for w in common.TABLEAU_WORKBOOKS}
        existing_workbooks = self.list_workbooks(project_id=publisher.reports_project_id)
        existing_workbook_ids = set([workbook_id_lookup[w['name']] for w in existing_workbooks if w['name'] in workbook_id_lookup])
        workbook_tableau_id_lookup = {workbook_id_lookup[d['name']]: d['id'] for d in existing_workbooks if d['name'] in workbook_id_lookup}

        for workbook_id in existing_workbook_ids - required_workbook_ids:
            self.delete_workbook_from_project(workbook_tableau_id_lookup[workbook_id])

        for workbook_id in required_workbook_ids - existing_workbook_ids:
            self.add_workbook_to_project(publisher, workbook_id)

    def setup_account(self, publisher, create_new_login=False, username=None, password=None):

        # create project
        project_id = self.create_project(publisher.reports_project)

        # create group, user, and assign permissions
        group_id = None
        user_id = None
        if create_new_login:
            group_id = self.create_group(publisher.reports_project + " User Group")
            self.add_group_to_project(group_id, project_id)
            user_id = self.create_user(username)
            self.set_user_password(user_id, password)
            self.add_user_to_group(user_id, group_id)
            self.add_default_workbook_permissions_for_project(group_id, project_id)
            self.add_default_datasource_permissions_for_project(group_id, project_id)

        return project_id, group_id, user_id

    def check_report_for_data(self, view_url, export_value_name):
        file_handle, file_path = tempfile.mkstemp()
        subprocess.call([common.TABCMD, 'login'] + self._tabcmd_login_params())
        subprocess.call([common.TABCMD, 'export', view_url[:view_url.index('?')], '--csv', '-f', file_path] + self._tabcmd_login_params())

        num_records = 0
        try:
            with open(file_path) as f:
                reader = csv.DictReader(f)
                line = next(reader)
                num_records = int(str(line[export_value_name].replace(',', '')))
        except:
            # swallow everything, assume the worst
            pass

        os.remove(file_path)

        return num_records > 0

    def generate_pdf_report(self, view_url, path=None):
        if not path:
            timestamp = str(int(datetime.datetime.now().timestamp()))
            path = os.path.join(common.TMP_DIR, '%s-%s.pdf' % (view_url[:view_url.index('?')].replace('/', '-'), timestamp))
        subprocess.call([common.TABCMD, 'login'] + self._tabcmd_login_params())
        subprocess.call([common.TABCMD, 'export', view_url, '--pdf', '-f', path] + self._tabcmd_login_params())
        return path
