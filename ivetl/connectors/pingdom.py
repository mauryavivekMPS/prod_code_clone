import csv
import time
import re
import requests
from ivetl.connectors.base import BaseConnector, MaxTriesAPIError


class PingdomConnector(BaseConnector):
    SERVER = 'https://api.pingdom.com'
    API_PATH = '/api/2.0'

    max_attempts = 5
    request_timeout = 30

    def __init__(self, email, password, api_key, tlogger=None):
        self.email = email
        self.password = password
        self.api_key = api_key
        self.base_url = self.SERVER + self.API_PATH
        self.tlogger = tlogger

    def _get_with_retry(self, path):
        attempt = 0
        success = False
        response = None
        while not success and attempt < self.max_attempts:
            try:
                response = requests.get(self.base_url + path, auth=(self.email, self.password), headers={'App-Key': self.api_key})
                response.raise_for_status()
                success = True
            except requests.HTTPError as http_error:
                if http_error.response.status_code == requests.codes.NOT_FOUND:
                    return {}
                if http_error.response.status_code == requests.codes.REQUEST_TIMEOUT or http_error.response.status_code == requests.codes.UNAUTHORIZED:
                    self._log("Pingdom API timed out. Trying again...")
                    attempt += 1
                elif http_error.response.status_code == requests.codes.INTERNAL_SERVER_ERROR or http_error.response.status_code == requests.codes.BAD_GATEWAY:
                    self._log("Pingdom API 500 error. Trying again...")
                    attempt += 1
                else:
                    raise http_error
            except Exception:
                    self._log("General Exception - Pingdom API failed. Trying again...")
                    attempt += 1

        if not success:
            raise MaxTriesAPIError(self.max_attempts)

        if response:
            return response.json()
        else:
            return {}

    def _log(self, message):
        if self.tlogger:
            self.tlogger.info(message)
        else:
            print(message)

    def get_checks(self):
        checks = []
        i = 0
        for check in self._get_with_retry('/checks')['checks']:
            checks.append(self._get_with_retry('/checks/%s' % check['id'])['check'])
            i += 1
            time.sleep(0.2)  # to prevent the API from throttling us
            print('doing check %s %s' % (i, check['id']))
        return checks


def pingdom_pipeline():

    fieldnames = (
        'sort_name',
        'site_id',
        'site_code',
        'name',
        'site_abbr',
        'print_issn',
        'online_issn',
        'publisher',
        'site_url',
        'umbrella_code',
        'umbrella_url',
        'usage_rpts_feature',
        'journal_info_feature',
        'ac_machine',
        'ac_syb_server',
        'ac_db',
        'ac_port',
        'journal_DOI',
        'counter_code',
        'dw_syb_server',
        'dw_db',
        'content_db',
        'content_syb_server',
        'subman_url',
        'legacy_type',
        'legacy_date',
        'dw_site_type',
        'is_book',
        'has_athens',
        'sage_subject_area')

    metadata_by_site_url = {}
    metadata_by_site_code = {}
    with open('/iv/hwdw-metadata/journalinfo/hwdw_journal_info.txt') as highwire_metadata_file:
        reader = csv.DictReader(highwire_metadata_file, delimiter='\t', fieldnames=fieldnames)
        for row in reader:
            metadata_by_site_url[row['site_url'][7:]] = row
            metadata_by_site_code[row['site_code']] = row

    pingdom_accounts = (
        {
            'name': 'primary',
            'email': 'pingdom@highwire.stanford.edu',
            'password': '#hq77C;_-',
            'api_key': '3j65ak0jedmwy1cu6u68u237a6a47quq'
        },
        {
            'name': 'secondary',
            'email': 'sysadmin@highwire.org',
            'password': '#[~Iw&+J6',
            'api_key': '9jl17p9dka6agqmwb6ru6e7mqt9ei8a1',
        },
    )

    total = 0
    by_hostname = 0
    by_site_code = 0
    with_www = 0

    all_checks = []
    for account in pingdom_accounts:
        pingdom = PingdomConnector(account['email'], account['password'], account['api_key'])
        for check in pingdom.get_checks():
            check['account'] = account['name']

            #
            # join the checks with the metadata
            #

            hostname = check['hostname']
            hostname_with_www = 'www.' + hostname

            total += 1

            metadata = None

            if hostname in metadata_by_site_url:
                metadata = metadata_by_site_url[hostname]
                by_hostname += 1

            elif hostname.startswith('submit'):
                site_code_without_prefix = check['site_code'].lstrip('bp_')
                if site_code_without_prefix in metadata_by_site_code:
                    metadata = metadata_by_site_code[site_code_without_prefix]
                    by_site_code += 1

            elif hostname_with_www in metadata_by_site_url:
                metadata = metadata_by_site_url[hostname_with_www]
                with_www += 1

            #
            # classify type of check
            #

            if metadata:
                check['site_name'] = metadata['name']
                check['site_code'] = metadata['site_code']
                check['publisher_name'] = metadata['publisher']
                check['publisher_code'] = metadata['umbrella_code']
            else:
                check['site_name'] = 'Unknown'
                check['site_code'] = 'unknown'
                check['publisher_name'] = ''
                check['publisher_code'] = ''

            name = check['name']
            url = check['type']['http']['url']
            if name.endswith('TOC'):
                check_type = 'toc'
            elif name.endswith('Article') or ('content' in url and url != '/content/current'):
                check_type = 'article'
            elif name.endswith('Search') or 'search' in url:
                check_type = 'search'
            elif account['name'] == 'primary' and 'content' not in url and 'search' not in url and not re.search('\d', url):
                check_type = 'home'
            else:
                check_type = 'other'

            check['check_type'] = check_type

            #
            # classify type of site
            #

            site_type = 'unknown'
            if metadata:
                if metadata['is_book'] == 'Y':
                    site_type = 'book'
                elif hostname.startswith('submit'):
                    site_type = 'benchpress'
                elif metadata['site_code'] == metadata['umbrella_code']:
                    site_type = 'umbrella'
                else:
                    site_type = 'journal'

            check['site_type'] = site_type

            #
            # classify platform
            #

            site_platform = 'unknown'
            if metadata:
                dw_site_type = metadata['dw_site_type']
                if dw_site_type:
                    site_platform = dw_site_type

            check['site_platform'] = site_platform

            all_checks.append(check)

            print(name, check_type, site_type, site_platform)

    print('total: %s' % total)
    print('by hostname: %s' % by_hostname)
    print('by site code: %s' % by_site_code)
    print('with www: %s' % with_www)
