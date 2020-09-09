import os
import re
import csv
import untangle
import requests
import subprocess
import time
import tempfile
import datetime
import logging
from requests.packages.urllib3.fields import RequestField
from requests.packages.urllib3.filepost import encode_multipart_formdata
from urllib.parse import quote_plus
from ivetl.common import common
from ivetl.connectors.base import BaseConnector, AuthorizationAPIError
from ivetl.models import PublisherMetadata

class TableauConnector(BaseConnector):
    request_timeout = 120
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
        url = self.server_url + "/api/3.6/auth/signin"

        request_string = """
            <tsRequest>
              <credentials name="%s" password="%s" >
                <site contentUrl="" />
              </credentials>
            </tsRequest>
        """

        self.signed_in = False

        try:
            response = requests.post(url,
                data=request_string % (self.username, self.password),
                timeout=self.request_timeout)
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
        url = self.server_url + "/api/3.6/sites/%s/projects" % self.site_id

        request_string = """
            <tsRequest>
              <project name="%s" />
            </tsRequest>
        """

        response = requests.post(url,
            data=request_string % project_name,
            headers={'X-Tableau-Auth': self.token},
            timeout=self.request_timeout)
        response.raise_for_status()

        r = untangle.parse(response.text).tsResponse
        project_id = r.project['id']
        return project_id

    def create_group(self, group_name):
        self._check_authentication()
        url = self.server_url + "/api/3.6/sites/%s/groups" % self.site_id

        request_string = """
            <tsRequest>
              <group name="%s" />
            </tsRequest>
        """

        response = requests.post(url,
            data=request_string % group_name,
            headers={'X-Tableau-Auth': self.token},
            timeout=self.request_timeout)
        response.raise_for_status()

        r = untangle.parse(response.text).tsResponse
        group_id = r.group['id']

        return group_id

    def add_group_to_project(self, group_id, project_id):
        self._check_authentication()
        url = self.server_url + "/api/3.6/sites/%s/projects/%s/permissions" % (self.site_id, project_id)

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

        response = requests.put(url,
            data=request_string % (project_id, group_id),
            headers={'X-Tableau-Auth': self.token},
            timeout=self.request_timeout)
        response.raise_for_status()

    def add_default_workbook_permissions_for_project(self, group_id, project_id):
        self._check_authentication()
        url = self.server_url + "/api/3.6/sites/%s/projects/%s/default-permissions/workbooks" % (self.site_id, project_id)

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

        response = requests.put(url,
            data=request_string % (project_id, group_id),
            headers={'X-Tableau-Auth': self.token},
            timeout=self.request_timeout)
        response.raise_for_status()

    def add_default_datasource_permissions_for_project(self, group_id, project_id):
        self._check_authentication()
        url = self.server_url + "/api/3.6/sites/%s/projects/%s/default-permissions/datasources" % (self.site_id, project_id)

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

        response = requests.put(url,
            data=request_string % (project_id, group_id),
            headers={'X-Tableau-Auth': self.token},
            timeout=self.request_timeout)
        response.raise_for_status()

    def create_user(self, username):
        self._check_authentication()
        url = self.server_url + "/api/3.6/sites/%s/users" % self.site_id

        request_string = """
            <tsRequest>
                <user name="%s" siteRole="Explorer" />
            </tsRequest>
        """

        response = requests.post(url,
            data=request_string % username,
            headers={'X-Tableau-Auth': self.token},
            timeout=self.request_timeout)
        response.raise_for_status()

        r = untangle.parse(response.text).tsResponse
        user_id = r.user['id']

        return user_id

    def set_user_password(self, user_id, password):
        self._check_authentication()
        url = self.server_url + "/api/3.6/sites/%s/users/%s" % (self.site_id, user_id)

        request_string = """
            <tsRequest>
                <user password="%s" />
            </tsRequest>
        """

        response = requests.put(url,
            data=request_string % password,
            headers={'X-Tableau-Auth': self.token})
        response.raise_for_status()

    def add_user_to_group(self, user_id, group_id):
        self._check_authentication()
        url = self.server_url + "/api/3.6/sites/%s/groups/%s/users" % (self.site_id, group_id)

        request_string = """
            <tsRequest>
                <user id="%s" />
            </tsRequest>
        """

        response = requests.post(url,
            data=request_string % user_id,
            headers={'X-Tableau-Auth': self.token},
            timeout=self.request_timeout)
        response.raise_for_status()

    def list_account_things(self):
        self._check_authentication()

        url = self.server_url + "/api/3.6/sites/%s/projects/" % self.site_id
        response = requests.get(url,
            headers={'X-Tableau-Auth': self.token},
            timeout=self.request_timeout)
        print(response.text)

        url = self.server_url + "/api/3.6/sites/%s/groups/" % self.site_id
        response = requests.get(url,
            headers={'X-Tableau-Auth': self.token},
            timeout=self.request_timeout)
        print(response.text)

        url = self.server_url + "/api/3.6/sites/%s/users/" % self.site_id
        response = requests.get(url,
            headers={'X-Tableau-Auth': self.token},
            timeout=self.request_timeout)
        print(response.text)

        url = self.server_url + "/api/3.6/sites/%s/datasources/" % self.site_id
        response = requests.get(url,
            headers={'X-Tableau-Auth': self.token},
            timeout=self.request_timeout)
        print(response.text)

        url = self.server_url + "/api/3.6/sites/%s/users/%s/workbooks/" % (self.site_id, self.user_id)
        response = requests.get(url,
            headers={'X-Tableau-Auth': self.token},
            timeout=self.request_timeout)
        print(response.text)

    def list_datasources(self, project_id=None):
        self._check_authentication()

        url = self.server_url + "/api/3.6/sites/%s/datasources" % self.site_id
        response = requests.get(url,
            params={'pageSize': 1000},
            headers={'X-Tableau-Auth': self.token},
            timeout=self.request_timeout)
        r = untangle.parse(response.text).tsResponse
        all_datasources = [{'name': d['name'], 'id': d['id'], 'project_id': d.project['id']} for d in r.datasources.datasource]

        if project_id:
            filtered_datasources = [d for d in all_datasources if d['project_id'] == project_id]
        else:
            filtered_datasources = all_datasources

        return filtered_datasources

    def list_datasources_by_names(self, ds_names, publisher=None):
        '''Given a *list* of human-readable datasource names,
        (e.g. article_citations_ds.tds),
        query Tableau Server for all datasources matching those in the list.
        Limiting the returned datasources to a set of names should
        signficantly reduce the data going over the wire compared to
        list_datasources().
        If a publisher_id is provided, filter out only that publisher's
        results by matching the Tableau Project Name (reports_project property)
        stored in the PublisherMetadata.
        Otherwise, return any datasources matching the given names.
        https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_datasources.htm#query_data_sources
        https://help.tableau.com/v2019.4/api/rest_api/en-us/REST/rest_api_concepts_filtering_and_sorting.htm#filter-expressions
        '''
        self._check_authentication()
        path = '/api/3.6/sites/%s/datasources' % self.site_id
        if publisher:
            project_name = publisher.reports_project
        else:
            project_name = None

        # if ds_names is empty, return an empty array (VIZOR-333)
        if not ds_names:
            return []

        ds_names_str = ','.join(ds_names)
        ds_filter = 'filter=name:in:[%s]&pageSize=1000' % ds_names_str
        url = self.server_url + path
        response = requests.get(url,
            params=ds_filter,
            headers={'X-Tableau-Auth': self.token},
            timeout=self.request_timeout)
        r = untangle.parse(response.text).tsResponse
        all_datasources = [{
            'name': d['name'],
            'id': d['id'],
            'project_id': d.project['id'],
            'project_name': d.project['name'],
        } for d in r.datasources.datasource]
        if project_name:
            filtered_datasources = [
                d for d in all_datasources if
                d['project_name'] == project_name
            ]
        else:
            filtered_datasources = all_datasources

        return filtered_datasources

    def list_workbooks(self, project_id=None):
        '''List workbooks. project_id is optional.
        If a project_id is provided, return only the workbooks for that project.
        Otherwise, return all workbooks in the configured site.
        The configured site_id and user_id are determined based on the login
        credentials provided to configure the tableau connector.
        '''
        self._check_authentication()

        url = self.server_url + "/api/3.6/sites/%s/users/%s/workbooks" % (self.site_id, self.user_id)
        response = requests.get(url,
            params={'pageSize': 1000},
            headers={'X-Tableau-Auth': self.token},
            timeout=self.request_timeout)
        r = untangle.parse(response.text).tsResponse
        all_workbooks = [{'name': d['name'], 'id': d['id'], 'project_id': d.project['id'], 'url': d['contentUrl']} for d in r.workbooks.workbook]

        if project_id:
            filtered_workbooks = [w for w in all_workbooks if w['project_id'] == project_id]
        else:
            filtered_workbooks = all_workbooks

        return filtered_workbooks

    def list_workbooks_by_name(self, wb_name, publisher_id=None):
        '''Given a human-readable workbook name
        (e.g. alert_hot_article_tracker_export.twb),
        query Tableau Server for the list of all workbooks with that name.
        Limiting the returned workbooks to a single name should
        signficantly reduce the data going over the wire compared to
        list_workbooks().
        If a publisher_id is provided, filter out only that publisher's
        results by matching the Tableau Project Name (reports_project property)
        stored in the PublisherMetadata.
        Otherwise, return all workbooks matching the given name.
        https://help.tableau.com/v2019.4/api/rest_api/en-us/REST/rest_api_ref_workbooksviews.htm#query_workbooks_for_site
        https://help.tableau.com/v2019.4/api/rest_api/en-us/REST/rest_api_concepts_filtering_and_sorting.htm#filter-expressions
        '''
        self._check_authentication()
        path = '/api/3.6/sites/%s/workbooks' % self.site_id
        wbext = common.TABLEAU_WORKBOOK_FILE_EXTENSION
        if wb_name[-len(wbext):] == wbext:
            wb_name = self._base_workbook_name(wb_name)
        # params must be string, not dictionary,
        # because Tableau will return a 400 if the ":" is percent-encoded
        # https://stackoverflow.com/questions/23496750/how-to-prevent-python-requests-from-percent-encoding-my-urls/23497912
        url_params = 'filter=name:eq:%s&pageSize=1000' % quote_plus(wb_name)
        url = self.server_url + path
        response = requests.get(url,
            params=url_params,
            headers={'X-Tableau-Auth': self.token},
            timeout=self.request_timeout)
        response.raise_for_status()
        r = untangle.parse(response.text).tsResponse
        all_workbooks = [{
            'name': d['name'],
            'id': d['id'],
            'project_id': d.project['id'],
            'project_name': d.project['name'],
            'content_url': d['contentUrl'],
            'default_view_id': d['defaultViewId']
        } for d in r.workbooks.workbook]
        if publisher_id:
            publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)
            project_name = publisher.reports_project
            filtered_workbooks = [
                w for w in all_workbooks if
                w['project_name'] == project_name
            ]
        else:
            filtered_workbooks = all_workbooks

        return filtered_workbooks

    def view_by_publisher_workbook(self, workbook):
        '''Given a dictionary representing a workbook,
        such as that returned by list_workbooks_by_name,
        return the default_view_id property if present.
        This is the ID stored internally by Tableau Server and useful
        for API calls such as Query View PDF and Query View Data.
        The default_view_id is the main starting view for the workbook,
        such as "Overview", "Insepctor", etc.
        https://help.tableau.com/v2019.4/api/rest_api/en-us/REST/rest_api_ref_workbooksviews.htm#query_view_data
        https://help.tableau.com/v2019.4/api/rest_api/en-us/REST/rest_api_ref_workbooksviews.htm#query_view_pdf
        '''

        if 'default_view_id' in workbook:
            return workbook['default_view_id']
        else:
            return None

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

    def refresh_data_source(self, datasource_id):
        '''https://help.tableau.com/v2019.4/api/rest_api/en-us/REST/rest_api_ref_datasources.htm#update_data_source_now
        POST /api/api-version/sites/site-id/datasources/datasource-id/refresh
        Refresh a datasource by its tableau id.
        '''
        self._check_authentication()
        path_params = (self.site_id, datasource_id)
        path = "/api/3.6/sites/%s/datasources/%s/refresh" % path_params
        url = self.server_url + path
        request_body = '<tsRequest></tsRequest>'
        try:
            response = requests.post(url,
                headers={'X-Tableau-Auth': self.token},
                data=request_body,
                timeout=self.request_timeout)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.info('HTTPError for url: %s' % url)
            logging.info(e)
            logging.info(response.text)
            raise e

    def create_extract(self, tableau_datasource_id):
        '''Create an extract for the provided datasource on Tableau Server.
        Tableau Server will queue up a process to create the extract
        on the server using the server's resources. 
        '''
        self._check_authentication()
        path_params = (self.site_id, tableau_datasource_id)
        path = "/api/3.6/sites/%s/datasources/%s/createExtract" % path_params
        url = self.server_url + path
        try:
            response = requests.post(url,
                headers={'X-Tableau-Auth': self.token},
                timeout=self.request_timeout)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.info('HTTPError for url: %s' % url)
            logging.info(e)
            logging.info(response.text)
            raise e

    def delete_datasource_from_project(self, tableau_datasource_id):
        self._check_authentication()
        url = self.server_url + "/api/3.6/sites/%s/datasources/%s" % (self.site_id, tableau_datasource_id)
        requests.delete(url, headers={'X-Tableau-Auth': self.token})

    def delete_workbook_from_project(self, tableau_workbook_id):
        self._check_authentication()
        url = self.server_url + "/api/3.6/sites/%s/workbooks/%s" % (self.site_id, tableau_workbook_id)
        requests.delete(url, headers={'X-Tableau-Auth': self.token})

    def add_datasource_to_project(self, publisher, datasource_id):
        self._check_authentication()
        path = "/api/3.6/sites/%s/datasources?overwrite=true" % self.site_id
        url = self.server_url + path

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

        # this first sub uses a negative lookback, i.e. replace base_datasource_name only when it's _not_ preceded by the dummy dir name
        prepared_datasource = re.sub(r'(?<!%s(\\|/))%s' % (common.TABLEAU_DUMMY_EXTRACTS_DIR_NAME, base_datasource_name), publisher_datasource_name, template)
        prepared_datasource = prepared_datasource.replace('&apos;%s&apos;' % common.TABLEAU_TEMPLATE_PUBLISHER_ID_TO_REPLACE, '&apos;%s&apos;' % publisher.publisher_id)

        with open(os.path.join(common.TMP_DIR,
            publisher_datasource_name +
            common.TABLEAU_DATASOURCE_FILE_EXTENSION),
            'w', encoding='utf-8', newline='\r\n') as fh:
            fh.write(prepared_datasource)

        with open(os.path.join(common.TMP_DIR,
            publisher_datasource_name +
            common.TABLEAU_DATASOURCE_FILE_EXTENSION),
            'rb') as fh:
            prepared_datasource_binary = fh.read()

        payload, content_type = self._make_multipart({
            'request_payload': ('', request_string % (publisher_datasource_name, publisher.reports_project_id), 'text/xml'),
            'tableau_datasource': (publisher_datasource_name + common.TABLEAU_DATASOURCE_FILE_EXTENSION, prepared_datasource_binary, 'application/octet-stream'),
        })
        try:
            response = requests.post(url,
                data=payload,
                headers={'X-Tableau-Auth': self.token, 'content-type': content_type})
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.info('HTTPError for url: %s' % url)
            logging.info(e)
            logging.info(request_string % (publisher_datasource_name, publisher.reports_project_id))
            logging.info(response.text)
            raise e
        except requests.exceptions.RequestException as e:
            logging.info('RequestException for url: %s' % url)
            logging.info(e)
            logging.info(request_string % (publisher_datasource_name, publisher.reports_project_id))
            logging.info(response.text)
            raise e
        except:
            raise
        r = untangle.parse(response.text).tsResponse

        datasource_tableau_id = r.datasource['id']

        return {
            'tableau_id': datasource_tableau_id,
        }

    def add_workbook_to_project(self, publisher, workbook_id):
        self._check_authentication()
        path_params = '?overwrite=true&workbookType=twb'
        path = '/api/3.6/sites/%s/workbooks%s' % (self.site_id, path_params)
        url = self.server_url + path

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

        response = requests.post(url,
            data=payload,
            headers={'X-Tableau-Auth': self.token, 'content-type': content_type})
        response.raise_for_status()

        r = untangle.parse(response.text).tsResponse

        workbook_url = r.workbook['contentUrl']
        workbook_tableau_id = r.workbook['id']

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
            url = self.server_url + "/api/3.6/sites/%s/workbooks/%s/permissions/groups/%s/%s/Allow" % (
                self.site_id,
                workbook_tableau_id,
                group_id,
                capability
            )
            requests.delete(url, headers={'X-Tableau-Auth': self.token})

    def update_datasources_and_workbooks(self, publisher):
        logging.info('update_datasources_and_workbooks for: %s' % publisher.publisher_id)
        logging.info('publisher.supported_product_groups = %s' % publisher.supported_product_groups)

        required_datasource_ids = set()
        for product_group_id in publisher.supported_product_groups:
            for datasource_id in common.PRODUCT_GROUP_BY_ID[product_group_id]['tableau_datasources']:
                required_datasource_ids.add(datasource_id)

        logging.info('required_datasource_ids = %s' % required_datasource_ids)

        existing_datasources = self.list_datasources(project_id=publisher.reports_project_id)
        existing_datasource_ids = set([self._base_datasource_name_from_publisher_name(publisher, d['name']) for d in existing_datasources])
        datasource_tableau_id_lookup = {self._base_datasource_name_from_publisher_name(publisher, d['name']): d['id'] for d in existing_datasources}

        for datasource_id in existing_datasource_ids - required_datasource_ids:
            logging.info('deleting datasource: %s' % datasource_id)
            self.delete_datasource_from_project(datasource_tableau_id_lookup[datasource_id])

        for datasource_id in required_datasource_ids - existing_datasource_ids:
            logging.info('adding datasource: %s' % datasource_id)
            tableau_datasource = self.add_datasource_to_project(publisher,
                datasource_id)
            self.create_extract(tableau_datasource['tableau_id'])

        time.sleep(10)

        required_workbook_ids = set()
        for product_group_id in publisher.supported_product_groups:
            for workbook_id in common.PRODUCT_GROUP_BY_ID[product_group_id]['tableau_workbooks']:
                required_workbook_ids.add(workbook_id)

        logging.info('required_workbook_ids = %s' % required_workbook_ids)

        existing_workbooks = self.list_workbooks(project_id=publisher.reports_project_id)
        existing_workbook_ids = set([common.TABLEAU_WORKBOOK_ID_BY_NAME[w['name']] for w in existing_workbooks if w['name'] in common.TABLEAU_WORKBOOK_ID_BY_NAME])
        workbook_tableau_id_lookup = {common.TABLEAU_WORKBOOK_ID_BY_NAME[d['name']]: d['id'] for d in existing_workbooks if d['name'] in common.TABLEAU_WORKBOOK_ID_BY_NAME}

        for workbook_id in existing_workbook_ids - required_workbook_ids:
            logging.info('deleting workbook: %s' % workbook_id)
            self.delete_workbook_from_project(workbook_tableau_id_lookup[workbook_id])

        for workbook_id in required_workbook_ids - existing_workbook_ids:
            logging.info('adding workbook: %s' % workbook_id)
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

    def check_report_for_data(self, view_id, export_value_name):
        # https://help.tableau.com/v2019.4/api/rest_api/en-us/REST/rest_api_ref_workbooksviews.htm#query_view_data
        # GET /api/api-version/sites/site-id/views/view-id/data
        file_handle, file_path = tempfile.mkstemp()
        # subprocess.call([common.TABCMD, 'login'] + self._tabcmd_login_params())
        # subprocess.call([common.TABCMD, 'export', view_url[:view_url.index('?')], '--csv', '-f', file_path] + self._tabcmd_login_params())
        path_params = (self.site_id, view_id)
        path = '/api/3.6/sites/%s/views/%s/data' % path_params
        url = self.server_url + path
        num_records = 0
        try:
            response = requests.get(url,
                headers={'X-Tableau-Auth': self.token},
                timeout=self.request_timeout)
            response.raise_for_status()
            with open(file_path, 'w') as f:
                f.write(response.content)
                f.close()
            with open(file_path) as f:
                reader = csv.DictReader(f)
                line = next(reader)
                num_records = int(str(line[export_value_name].replace(',', '')))
        except requests.exceptions.HTTPError as e:
            logging.info('HTTPError for url: %s' % url)
            logging.info(e)
            logging.info(response.text)
            pass

        os.remove(file_path)

        return num_records > 0

    def generate_pdf_report(self, view_id, path=None):
        # https://help.tableau.com/v2019.4/api/rest_api/en-us/REST/rest_api_ref_workbooksviews.htm#query_view_pdf
        # GET /api/api-version/sites/site-id/views/view-id/pdf
        if not path:
            timestamp = str(int(datetime.datetime.now().timestamp()))
            path = os.path.join(common.TMP_DIR, '%s-%s.pdf' % (view_id, timestamp))
        # subprocess.call([common.TABCMD, 'login'] + self._tabcmd_login_params())
        # subprocess.call([common.TABCMD, 'export', view_url, '--pdf', '-f', path] + self._tabcmd_login_params())
        url_path_params = (self.site_id, view_id)
        url_path = '/api/3.6/sites/%s/views/%s/pdf' % url_path_params
        url = self.server_url + url_path
        logging.debug('generate_pdf_report for url: %s' % url)
        try:
            response = requests.get(url,
                headers={'X-Tableau-Auth': self.token},
                timeout=self.request_timeout)
            response.raise_for_status()
            with open(path, 'wb') as f:
                f.write(response.content)
                f.close()
        except requests.exceptions.HTTPError as e:
            logging.info('HTTPError for url: %s' % url)
            logging.info(e)
            logging.info(response.text)
            pass
        return path

    def list_projects(self):
        self._check_authentication()
        url = self.server_url + "/api/3.6/sites/%s/projects" % self.site_id

        try:
            response = requests.get(url,
                params={'pageSize': 1000},
                headers={'X-Tableau-Auth': self.token},
                timeout=self.request_timeout)
            response.raise_for_status()
            r = untangle.parse(response.text).tsResponse
            all_projects = [
                {
                    'name': p['name'],
                    'id': p['id'],
                    'description': p['description'],
                    'permissions': p['contentPermissions']
                } for p in r.projects.project
            ]
            return all_projects
        except requests.exceptions.HTTPError as e:
            logging.info('HTTPError for url: %s' % url)
            logging.info(e)
        except requests.exceptions.RequestException as e:
            logging.info('RequestException for url: %s' % url)
            logging.info(e)

    def list_groups(self):
        self._check_authentication()
        url = self.server_url + "/api/3.6/sites/%s/groups" % self.site_id

        try:
            response = requests.get(url,
                params={'pageSize': 1000},
                headers={'X-Tableau-Auth': self.token},
                timeout=self.request_timeout)
            response.raise_for_status()
            r = untangle.parse(response.text).tsResponse
            all_groups = [
                {
                    'name': g['name'],
                    'id': g['id']
                } for g in r.groups.group
            ]
            return all_groups
        except requests.exceptions.HTTPError as e:
            logging.info('HTTPError for url: %s' % url)
            logging.info(e)
        except requests.exceptions.RequestException as e:
            logging.info('RequestException for url: %s' % url)
            logging.info(e)

    def list_users(self):
        self._check_authentication()
        url = self.server_url + "/api/3.6/sites/%s/users" % self.site_id

        try:
            response = requests.get(url,
                params={'pageSize': 1000},
                headers={'X-Tableau-Auth': self.token},
                timeout=self.request_timeout)
            response.raise_for_status()
            r = untangle.parse(response.text).tsResponse
            all_users = [
                {
                    'name': u['name'],
                    'id': u['id'],
                    'site_role': u['siteRole'],
                    'last_login': u['lastLogin']
                } for u in r.users.user
            ]
            return all_users
        except requests.exceptions.HTTPError as e:
            logging.info('HTTPError for url: %s' % url)
            logging.info(e)
        except requests.exceptions.RequestException as e:
            logging.info('RequestException for url: %s' % url)
            logging.info(e)
