#!/usr/bin/env python

import re
import requests

def get_key():
    cookie_url = 'https://dev.elsevier.com/user/registration'
    cookie_response = requests.get(cookie_url)
    cookies = cookie_response.cookies

    registration_url = 'https://dev.elsevier.com/user/registration'
    registration_params = {
        'firstName': 'Pub 10',
        'lastName': 'Highwire',
        'emailAddress': 'nmehta-pubid10@highwire.com',
        'password': 'highwire01',
        'confirmPassword': 'highwire01',
        'registerUseragreement': 'true',
    }
    registration_response = requests.post(registration_url, data=registration_params, cookies=cookies)

    sign_in_url = 'https://dev.elsevier.com/apikey/manage'
    sign_in_params = {
        'inputEmail': 'nmehta-pubid08@highwire.com',
        'inputPassword': 'highwire01',
        'rememberMe': '',
    }
    sign_in_response = requests.post(sign_in_url, data=sign_in_params, cookies=cookies)

    keys = []

    for i in range(1, 6):
        key_name = 'Key %s' % i
        key_url = 'http://manage.vizors.org'
        create_key_url = 'https://dev.elsevier.com/apikey/create'
        create_key_params = {
            'projectName': key_name,
            'websiteURL': 'http://manage.vizors.org',
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

        keys.append(m.groups()[0])

    print(keys)

if __name__ == "__main__":
    get_key()
