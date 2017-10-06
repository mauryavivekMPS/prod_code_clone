import re
import math
import traceback
import requests
import logging
from ivetl.models import PublisherMetadata
from ivetl.celery import app

log = logging.getLogger(__name__)


@app.task
def get_scopus_api_keys(publisher_id, num_keys=10):
    log.info('Starting scopus API key retrieval for %s...' % publisher_id)
    keys = []

    PublisherMetadata.objects(publisher_id=publisher_id).update(
        scopus_key_setup_status='in-progress',
    )

    try:
        max_keys_per_account = 10
        num_accounts = math.ceil(num_keys / max_keys_per_account)  # type: int
        num_keys_left_to_get = num_keys

        for account_index in range(num_accounts):

            # load a page to get session ID cookies
            cookie_url = 'https://dev.elsevier.com/user/registration'
            cookie_response = requests.get(cookie_url)
            cookies = cookie_response.cookies

            # register a developer account
            email = 'nmehta-%s-%s@highwire.org' % (publisher_id, account_index)
            password = 'highwire01'
            registration_url = 'https://dev.elsevier.com/user/registration'
            registration_params = {
                'firstName': 'Neil',
                'lastName': 'Mehta',
                'emailAddress': email,
                'password': password,
                'confirmPassword': password,
                'registerUseragreement': 'true',
            }
            requests.post(registration_url, data=registration_params, cookies=cookies)

            # sign in with the new account
            sign_in_url = 'https://dev.elsevier.com/apikey/manage'
            sign_in_params = {
                'inputEmail': email,
                'inputPassword': password,
                'rememberMe': '',
            }
            requests.post(sign_in_url, data=sign_in_params, cookies=cookies)

            if num_keys_left_to_get > 10:
                num_keys_for_this_account = 10
            else:
                num_keys_for_this_account = num_keys_left_to_get

            num_keys_left_to_get -= num_keys_for_this_account

            # create a set of keys
            for i in range(1, num_keys_for_this_account + 1):
                key_name = '%s %s' % (publisher_id, i)
                key_url = 'http://%s-%s-%s.vizors.org' % (publisher_id, account_index, i)
                create_key_url = 'https://dev.elsevier.com/apikey/create'
                create_key_params = {
                    'projectName': key_name,
                    'websiteURL': key_url,
                    'agreed': 'true',
                    'textminingAgreed': 'true',
                    'mode': 'Insert',
                    'apiKey': '',
                    'mappingType': 'website',
                }
                create_key_response = requests.post(create_key_url, data=create_key_params, cookies=cookies)

                m = re.search(
                    r'<a href="javascript:changeMode\(\'Update\',\'(\w+)\',\'%s\',\'%s\'' % (key_url, key_name),
                    create_key_response.text,
                    flags=re.MULTILINE
                )
                match_groups = m.groups()
                if not match_groups:
                    log.error('No matches from the HTML regex to pull out the new API key.')
                    raise Exception('Regular expression to pull out new API key failed.')

                keys.append(m.groups()[0])

        PublisherMetadata.objects(publisher_id=publisher_id).update(
            scopus_key_setup_status='completed',
        )

        log.info('Completed key retrieval')

    except:
        print('Error in scopus API key retrieval:')
        print(traceback.format_exc())

        PublisherMetadata.objects(publisher_id=publisher_id).update(
            scopus_key_setup_status='error',
        )

    if keys:
        log.info('Saving %s keys to %s' % (len(keys), publisher_id))
        PublisherMetadata.objects(
            publisher_id=publisher_id,
        ).update(
            scopus_api_keys=keys,
        )
