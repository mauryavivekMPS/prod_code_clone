import csv
import requests
from ivetl.connectors.base import BaseConnector


class PingdomConnector(BaseConnector):

    def __init__(self, email, password, api_key, server):
        self.email = email
        self.password = password
        self.api_key = api_key
        self.base_url = server + '/api/2.0'

    def _get(self, path):
        response = requests.get(self.base_url + path, auth=(self.email, self.password), headers={'App-Key': self.api_key})
        response.raise_for_status()
        return response.json()

    def get_checks(self):
        checks = []
        for check in self._get('/checks')['checks'][:5]:
            checks.append(self._get('/checks/%s' % check['id'])['check'])
        return checks


def pingdom_pipeline():

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

    server = 'https://api.pingdom.com'

    all_checks = []
    for account in pingdom_accounts:
        pingdom = PingdomConnector(account['email'], account['password'], account['api_key'], server)
        for check in pingdom.get_checks():
            check['account'] = account['name']
            all_checks.append(check)

            if check['hostname'] == 'scnotes.sepmonline.org':
                print(check)



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

    metadata_lookup = {}
    with open('/iv/hwdw-metadata/journalinfo/hwdw_journal_info.txt') as highwire_metadata_file:
        reader = csv.DictReader(highwire_metadata_file, delimiter='\t', fieldnames=fieldnames)
        for row in reader:
            # if row['site_url'] in metadata_lookup:

                # print(row)

            metadata_lookup[row['site_url']] = row

