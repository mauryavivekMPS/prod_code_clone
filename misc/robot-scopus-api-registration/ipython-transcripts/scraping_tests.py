# Note: This file is not meant to run or do anything, it was a record of the various (unsuccessful) attempts to use a
# software robot to register and get Scopus API keys.

register_url = 'https://www.developers.elsevier.com/action/customer/profile'
import requests
register_params = {
    'first_name': 'John',
    'last_name': 'Smith',
    'email_address': 'jm1@lonepixel.com',
    'password': 'test12',
    'confirmPassword': 'test12',
    'organization_name': 'HW1',
    'organization_type': '42',
    'user_role': '14',
    'subject_area': ['5', '6'],
    'subject_areas': '5,6',
    'have_read_user_agreement': 'true',
    'registerButton': 'Register',
    'reg_type': 'Guest',
    'http_method_name': 'POST',
    'opaque_info_value': 'This is opaque info',
    'anon_type': 'ANON_GUEST',
}
register_response = requests.post(register_url, data=register_params)
register_response = requests.post(register_url, data=register_params)
r = register_response
r.status_code
r.content
r.url
'success' in r.text
r.cookies
init_cookies_url = 'http://www.developers.elsevier.com/action/devprojects?originPage=devportal'
init_cookies_response = requests.get(init_cookies_url)
init_cookies_response.text
init_cookies_response.cookies
init_cookies_response.status_code
init_cookies_response.url
init_cookies_response.cookies
init_cookies_response.headers
init_cookies_response.is_redirect
init_cookies_response.is_permanent_redirect
init_cookie_headers = {
    'referer': 'http://dev.elsevier.com/myapikey.html',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36',
    'Upgrade-Insecure-Requests': '1',
}
init_cookies_response = requests.get(init_cookies_url, headers=init_cookie_headers)
init_cookies_response.is_redirect
init_cookies_response.headers
init_cookies_response.cookies
init_cookies_url
init_cookies_response = requests.get(init_cookies_url, headers=init_cookie_headers, allow_redirects=False)
init_cookies_response.cookies
str(init_cookies_response.cookies)
for c in init_cookies_response.cookies:
    print(c)
c = init_cookies_response.cookies[0]
cookies = dict(init_cookies_response.cookies)
cookies
register_response = requests.post(register_url, data=register_params, cookies=cookies, allow_redirects=False)
register_response.status_code
register_response.text
register_response.cookies
register_params
register_response.content
out = open('/Users/john/Desktop/out.html', 'w')
out.write(register_response.content)
out.write(register_response.text)
out.close()
register_params = {
    'first_name': 'John',
    'last_name': 'Smith',
    'email_address': 'jm1@lonepixel.com',
    'password': 'test12',
    'confirmPassword': 'test12',
    'organization_name': 'HW1',
    'organization_type': '42',
    'user_role': '14',
    'subject_area': ['5', '6'],
    'subject_areas': '5,6',
    'have_read_user_agreement': 'true',
    'registerButton': 'Register',
    'reg_type': 'Guest',
    'http_method_name': 'POST',
    'opaque_info_name': 'This is opaque info',
    'opaque_info_value': 'This is opaque info',
    'anon_type': 'ANON_GUEST',
}
register_response = requests.post(register_url, data=register_params, cookies=cookies, allow_redirects=False)
register_response = requests.post(register_url, data=register_params, cookies=cookies, allow_redirects=False)
register_response.content
register_response.status_code
'Registration successful' in register_response.text
register_response.cookies
register_cookies = dict(register_response.cookies)
register_cookies
site_url = 'http://www.developers.elsevier.com/action/devnewsite'
site_params = {
    'siteDetailVO.websiteURL': 'http://api-for-publisherid.com',
    'checkboxName': 'true',
    'addRegisteredSite': 'Register site',
    '_sourcePage': 'pKqJ_-hQBjCt6P0zUxElW0uPTJMsX9VKlGXWX3Vz-nJu8KU_qoSsbN9LgIJLqmlQZYTcUJsnO5g=',
    '__fp': 'KUn9ldcLagQ=',
}
site_response = requests.post(site_url, data=site_params, cookies=register_cookies, allow_redirects=False)
site_response.status_code
site_response.content
site_response.url
site_response.headers
site_response.raw
site_response.reason
site_response.json
site_response.is_redirect
r = requests.get('http://dev.elsevier.com/myapikey.html', cookies=register_cookies, allow_redirects=False)
r.status_code
r.text
out = open('/Users/john/Desktop/out.html', 'w')
out.write(r.content)
out.write(r.text)
out.close()
register_cookies
r = requests.get('http://www.developers.elsevier.com/action/devprojects', cookies=register_cookies)
r.status_code
r.cookies
r = requests.get('http://www.developers.elsevier.com/action/devprojects', cookies=register_cookies, allow_redirect=False)
r = requests.get('http://www.developers.elsevier.com/action/devprojects', cookies=register_cookies, allow_redirects=False)
r.status_code
r.cookies
cookies_for_site = dict(r.cookies)
site_response = requests.post(site_url, data=site_params, cookies=cookies_for_site, allow_redirects=False)
site_response.url
site_response.status_code
site_response.url
site_response.text
site_response = requests.post(site_url, data=site_params, cookies=cookies_for_site, allow_redirects=True)
site_response.text
out = open('/Users/john/Desktop/out.html', 'w')
out.write(site_response.text)
out.close()
r = requests.get('http://www.developers.elsevier.com/action/devprojects?originPage=devpor', cookies=cookies_for_site, allow_redirects=False)
r
r.text
out = open('/Users/john/Desktop/out.html', 'w')
out.write(r.text)
out.close()
login_params = {
    'username': 'jm1@lonepixel.com',
    'password': 'test12',
    'remember_flag': 'true',
    'submit': 'Login',
    'auth_type': 'LOGIN_PASSWORD',
    'http_method_name': 'POST',
    'isClaimingRemoteAccess': 'FALSE',
    'shibboleth_fence': 'false',
    'path_choice_exists': 'false',
    'acct_name': 'SciVerse Applications Guest',
    'dept_name': 'SciVerse Applications Guest',
    'cars_cookie_flag': 'true',
}
login_url = 'https://www.developers.elsevier.com/action/customer/authenticate'
r = requests.get(login_url, data=login_params, allow_redirects=True)
r = requests.get(login_url, data=login_params, allow_redirects=True)
r.cookies
r.text
out = open('/Users/john/Desktop/out.html', 'w')
out.write(r.text)
out.close()
r = requests.get(login_url, data=login_params, allow_redirects=False)
r.status_code
r.text
r.url
r.headers
r.text
r.url
r = requests.get(login_url, data=login_params, allow_redirects=True)
r.cookies
r = requests.get(login_url, data=login_params, allow_redirects=False)
r.is_redirect
r.reason
r.text
r.url
dict(r.headers)
r.raw
r.links
r = requests.get(login_url, data=login_params, allow_redirects=True)
r.history
r1 = r.history[0]
r1.cookies
r2 = r.history[1]
r2.cookies
r2.text
r1.text
r3 = r.history[2]
r3.cookies
r3.text
r2.cookies
r1.cookies
login_cookies = dict(r1.cookies)
site_response = requests.post(site_url, data=site_params, cookies=login_cookies, allow_redirects=True)
site_response.status_code
site_response.text
site_response.history
out = open('/Users/john/Desktop/out.html', 'w')
out.write(site_response.text)
out.close()
site_params
site_response = requests.post(site_url, data=site_params, cookies=login_cookies, allow_redirects=True)
login_cookies
test_cookies = test_cookies = {
    'CARS_COOKIE': '006B004800520046002B00750033003300320044006F0049005600630059004D00510031004C0038002B004700420046006600550062006600670038002B00520043005400310038006D004A0074004C006B00420067007300370070002F0030004A00460079007600570059006F00560070004C007300760041007A006F0063003200370037006200370042005A004B006A00530059003D',
    'JSESSIONID': 'E1CE23500568241669A789B7A61DBA0E.YIBSHE3YuWyllR45hLdYAw',
    'SESSIONID_COOKIE': 'E1CE23500568241669A789B7A61DBA0E.YIBSHE3YuWyllR45hLdYAw',
    'USER_ASSOCIATION_TYPE': 'GUEST',
    'USER_AUTH_TOKEN': '7f07-e119bcaf051243a2381-e246409670a6e52d',
    'USR_ANON_TYPE': 'INDIVIDUAL',
    'amp.machine.id.cookie': 'E8AC11BBE3B00F2925147E79CFE6F2EA.YIBSHE3YuWyllR45hLdYAw',
    'acw': '6f07-e119bcaf051243a2381-e246409670a6e52d%7C%24%7CcX0d4bTkfKLMRtv8MrRiQ83%2B%2BSd%2F3g8QeULT8P6L3yjxCXxQVdulvnlCXdC8pr7UR%2FOaE06pRdArpkEp0Gpwzki5a75AO5y6',
    'utt': '9a32-f2b431ec051f212ef196d9519b63fec0ec',
}
test_cookies
site_params
site_params['siteDetailVO.websiteURL'] = 'http://foo2-publisher.com'
site_params['_sourcePage'] = '8LE16waSlHw37DJURcrkNLYb9Gg7TE5WAJvHLWP0UTLnEXRH2nY6oLN1CrWI07yyZzvNixWqrVw='
site_params['__fp'] = 'tPy-oW0AemY='
site_response = requests.post(site_url, data=site_params, cookies=test_cookies, allow_redirects=True)
site_response.text
site_params['siteDetailVO.websiteURL'] = 'http://foo3-publisher.com'
site_response = requests.post(site_url, data=site_params, cookies=test_cookies, allow_redirects=True)
site_response.status_code
r.url
login_cookies = dict(r1.cookies)
r = requests.get(login_url, data=login_params, allow_redirects=True)
r = requests.get(login_url, data=login_params, allow_redirects=True)
r.history
r.history[0].cookies
r.history[1].cookies
r.history[1].url
r.history[0].url
r.history[2].url
r.history[0].url
r.history[0].cookies
r = requests.get(login_url, data=login_params, allow_redirects=False)
r = requests.get(login_url, data=login_params, allow_redirects=False)
r.status_code
r.headers
dict(r.headers)
login_url
r = requests.post(login_url, data=login_params, allow_redirects=False)
r.status_code
r.headers
login_params
login_params = {
    'username': 'jm1@lonepixel.com',
    'password': 'test12',
    'remember_flag': 'true',
    'remember_path_flag': 'false',
    'submit': 'Login',
    'auth_type': 'LOGIN_PASSWORD',
    'http_method_name': 'POST',
    'isClaimingRemoteAccess': 'FALSE',
    'shibboleth_fence': 'false',
    'path_choice_exists': 'false',
    'acct_name': 'SciVerse Applications Guest',
    'dept_name': 'SciVerse Applications Guest',
    'cars_cookie_flag': 'true',
    'path_choice': '',
}
r.cookies
first_attempt_login_cookies = dict(r.cookies)
r = requests.post(login_url, data=login_params, cookies=first_attempt_login_cookies, allow_redirects=False)
r.status_code
r.co
r.cookies
dict(r.headers)
r = requests.post(login_url, data=login_params, cookies=first_attempt_login_cookies, allow_redirects=True)
r.status_code
r.text
out = open('/Users/john/Desktop/out.html', 'w')
out.write(r.text)
out.close()
r.cookies
r = requests.post(login_url, data=login_params, cookies=first_attempt_login_cookies, allow_redirects=False)
r.cookies
dict(r.headers)
r2 = requests.get('http://www.developers.elsevier.com/action/customer/authenticate?__fsk=-342301287', cookies=r.cookies, allow_redirects=False)
r2.status_code
r2.cookies
r2 = requests.get('http://www.developers.elsevier.com/action/customer/authenticate?__fsk=-342301287', cookies=r.cookies, headers={'Referer': 'http://www.developers.elsevier.com/action/devprojects?originPage=devportal'}, allow_redirects=False)
r2.cookies
r = requests.post(login_url, data=login_params, allow_redirects=False)
dict(r.headers)
dict(r.cookies)
r1 = requests.post(login_url, data=login_params, cookies=r.cookies, allow_redirects=False)
dict(r.headers)
r.cookies
login_params
r = requests.post(login_url, data=login_params, allow_redirects=False)
r.text
dict(r.headers)
r_cookies = dict(r.cookies)
r_cookies
r1 = requests.post(login_url, data=login_params, cookies=r_cookies, allow_redirects=False)
r1.status_code
r1.cookies
r1.headers
r2 = requests.get('http://www.developers.elsevier.com/action/customer/authenticate?__fsk=-144883820', cookies=r_cookies, allow_redirects=False)
r2.status_code
r2.cookies
r_and_r1_cookies = r_cookies.copy()
r_and_r1_cookies.update(dict(r1.cookies))
r_and_r1_cookies
r1.cookies
r_and_r1_cookies
r.cookies
dict(r.cookies)
dict(r1.cookies)
r2 = requests.get('http://www.developers.elsevier.com/action/customer/authenticate', data={'__fsk': '-144883820'}, cookies=r_and_r1_cookies, allow_redirects=False)
r2.status_code
r2.cookies
rx = requests.get('http://www.developers.elsevier.com/action/devprojects', data={'originPageLogout': 'devportal', 'icr': 'true'}, cookies=r_and_r1_cookies, allow_redirects=False)
rx.status_code
rx.text
rx.cookies
ry = requests.get('http://dev.elsevier.com/myapikey.html')
ry.status_code
ry.cookies
ry = requests.get('http://dev.elsevier.com/myapikey.html', allow_redirects=False)
ry.cookies
ry.status_code
ry.text
ry = requests.get('http://dev.elsevier.com/myapikey.html', allow_redirects=False)
ry.text
'acw' in ry.text
ry.text
r_cookies
ry = requests.get('http://dev.elsevier.com/myapikey.html', cookies=r_cookies, allow_redirects=False)
ry
ry.e
'acw' in ry.text
r_cookies
r = requests.post(login_url, data=login_params, allow_redirects=False)
r = requests.post(login_url, data=login_params, allow_redirects=False)
r.cookies
dict(r.cookies)
r1 = requests.post(login_url, data=login_params, cookies=r.cookies, allow_redirects=False)
dict(r1.headers)
r.cookies
r_cookies
r0 = requests.get('http://www.developers.elsevier.com/action/devprojects', data={'originPage': 'devportal'}, cookies=r_cookies, allow_redirects=False)
r0.status_code
r0.cookies
r0.text
'acw' in r0.text
r0.links
out = open('/Users/john/Desktop/out.html', 'w')
out.write(r0.text)
out.close()
acw = '4393-3330f0bf051cfab7e27-95fc3f608dfa5832-oZ%7C%24%7CumresIc1OU2oWQTKI94MGkJ7y43dMtMHRGv%2FtGZQ8A%2BBSRjC9KomlJhELTTw2qVogo%2Bmh1JYdy217iOeR%2BqxTzEBlHPwVnckQF10CpAq8%2Bc%3D&amp'
utt = '303-0bd902bf0510334ffa17ff8b862fed73f6e'
dict(r.headers)
r1 = requests.post(login_url, data=login_params, cookies=r.cookies, allow_redirects=False)
r1 = requests.post(login_url, data=login_params, cookies=r.cookies, allow_redirects=False)
dict(r1.headers)
r1.cookies
dict(r1.cookies)
r1_cookies = dict(r1.cookies)
r1_cookies['acw'] = acw
r1_cookies['utt'] = utt
r1_cookies
dict(r1.headers)
r2 = requests.get('http://www.developers.elsevier.com/action/customer/authenticate', data={'__fsk': '1777432959'}, cookies=r1_cookies, allow_redirects=False)
r2.status_code
r2.text
r2.cookies
out = open('/Users/john/Desktop/out.html', 'w')
out.write(r2.text)
out.close()
r2 = requests.get('http://www.developers.elsevier.com/action/customer/authenticate', data={'__fsk': '1777432959'}, cookies=r1_cookies, allow_redirects=False)
r2.text
out = open('/Users/john/Desktop/out.html', 'w')
out.write(r0.text)
out.close()
ra = requests.get('http://acw.sciverse.com/SSOCore/update?acw=4393-3330f0bf051cfab7e27-95fc3f608dfa5832-oZ%7C%24%7CumresIc1OU2oWQTKI94MGkJ7y43dMtMHRGv%2FtGZQ8A%2BBSRjC9KomlJhELTTw2qVogo%2Bmh1JYdy217iOeR%2BqxTzEBlHPwVnckQF10CpAq8%2Bc%3D&amp;utt=303-0bd902bf0510334ffa17ff8b862fed73f6e')
ra
ra.text
ra.cookies
r2 = requests.get('http://www.developers.elsevier.com/action/customer/authenticate', data={'__fsk': '1777432959'}, cookies=r1_cookies, allow_redirects=False)
r2.text
r1_cookies
r2 = requests.get('http://www.developers.elsevier.com/action/customer/authenticate', data={'__fsk': '1777432959'}, cookies=r1_cookies, allow_redirects=False)
r2
r2 = requests.get('http://www.developers.elsevier.com/action/customer/authenticate?__fsk=1777432959', cookies=r1_cookies, allow_redirects=False)
r2
r1
r1.headers
r = requests.post(login_url, data=login_params, allow_redirects=False)
r.cookies
dict(r.cookies)
r0 = requests.get('http://www.developers.elsevier.com/action/devprojects', data={'originPage': 'devportal'}, cookies=r.cookies, allow_redirects=False)
r0.text
r0.cookies
dict(r0.cookies)
dict(r.cookies)
rx = requests.get('http://www.developers.elsevier.com/action/devprojects', data={'originPageLogout': 'devportal', 'icr': 'true'}, cookies=r.cookies, allow_redirects=False)
rx.cookies
rx.text
rx
rx = requests.get('http://www.developers.elsevier.com/action/devprojects', data={'originPageLogout': 'devportal', 'icr': 'true'}, cookies=dict(r.cookies), allow_redirects=False)
rx
rx.text
'acw' in rx.text
rx.cookies
r0.cookies
cookies_for_login = dict(r.cookies)
cookies_for_login['acw'] = '5c968549a0bf051133793f2-e66f6466a6a4ab28-A%7C%24%7C%2B5L1l03OsCi6HVFYe7E1dwCScPhYcyRCob%2BY7koGErWTw%2F2rIhZH2gWySn%2BLbt6Uo964FrUYH9cZ8utalqVg7i9JOLAXuNfe5ic3jrADPgQ%3D&amp'
cookies_for_login['utt'] = '6c968549a0bf051133793f2-e66f6466a6a4ab28-yV'
r1 = requests.post(login_url, data=login_params, cookies=cookies_for_login, allow_redirects=False)
r1
r1.cookies
dict(r1.headers)
r2 = requests.get('http://www.developers.elsevier.com/action/customer/authenticate?__fsk=-1948328288', headers={'Referer': 'http://www.developers.elsevier.com/action/devprojects?originPage=devportal'}, cookies=cookies_for_login, allow_redirects=False)
r2
r2 = requests.get('http://www.developers.elsevier.com/action/customer/authenticate', data={'__fsk': '-1948328288'}, headers={'Referer': 'http://www.developers.elsevier.com/action/devprojects?originPage=devportal'}, cookies=cookies_for_login, allow_redirects=False)
r2
r2 = requests.get('http://www.developers.elsevier.com/action/customer/authenticate', data={'__fsk': '-1948328288'}, headers={'Referer': 'http://www.developers.elsevier.com/action/devprojects?originPage=devportal', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.7 (KHTML, like Gecko) Version/9.0.1 Safari/601.2.7'}, cookies=cookies_for_login, allow_redirects=False)
r2
r2.request.body
r2.request.path_url
r2 = requests.get('http://www.developers.elsevier.com/action/customer/authenticate?__fsk=-1948328288', headers={'Referer': 'http://www.developers.elsevier.com/action/devprojects?originPage=devportal', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.7 (KHTML, like Gecko) Version/9.0.1 Safari/601.2.7'}, cookies=cookies_for_login, allow_redirects=False)
r2
r2.text
r2 = requests.get('http://www.developers.elsevier.com/action/customer/authenticate?__fsk=-1948328288', headers={'Referer': 'http://www.developers.elsevier.com/action/devprojects?originPage=devportal', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.7 (KHTML, like Gecko) Version/9.0.1 Safari/601.2.7'}, cookies=cookies_for_login, allow_redirects=True)
r2
r2.text
r2 = requests.post('http://www.developers.elsevier.com/action/customer/authenticate?__fsk=-1948328288', headers={'Referer': 'http://www.developers.elsevier.com/action/devprojects?originPage=devportal', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.7 (KHTML, like Gecko) Version/9.0.1 Safari/601.2.7'}, cookies=cookies_for_login, allow_redirects=True)
r2
r2.text
cookies_for_login
cookies_for_login['acw'] = '5c968549a0bf051133793f2-e66f6466a6a4ab28-A%7C%24%7C%2B5L1l03OsCi6HVFYe7E1dwCScPhYcyRCob%2BY7koGErWTw%2F2rIhZH2gWySn%2BLbt6Uo964FrUYH9cZ8utalqVg7i9JOLAXuNfe5ic3jrADPgQ%3D'
r2 = requests.post('http://www.developers.elsevier.com/action/customer/authenticate?__fsk=-1948328288', headers={'Referer': 'http://www.developers.elsevier.com/action/devprojects?originPage=devportal', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.7 (KHTML, like Gecko) Version/9.0.1 Safari/601.2.7'}, cookies=cookies_for_login, allow_redirects=True)
r2
r2.text
out = open('/Users/john/Desktop/out.html', 'w')
out.close()
out = open('/Users/john/Desktop/out2.html', 'w')
out.write(r2)
out.write(r2.text)
out.close()
r2 = requests.get('http://www.developers.elsevier.com/action/customer/authenticate?__fsk=-1948328288', headers={'Referer': 'http://www.developers.elsevier.com/action/devprojects?originPage=devportal', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.7 (KHTML, like Gecko) Version/9.0.1 Safari/601.2.7'}, cookies=cookies_for_login, allow_redirects=True)
r2
r2.text
out = open('/Users/john/Desktop/out2.html', 'w')
out.write(r2.text)
out.close()
r1 = requests.post(login_url, data=login_params, cookies=cookies_for_login, allow_redirects=False)
dict(r1.headers)
r2 = requests.get('http://www.developers.elsevier.com/action/customer/authenticate?__fsk=1036268231', headers={'Referer': 'http://www.developers.elsevier.com/action/devprojects?originPage=devportal', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.7 (KHTML, like Gecko) Version/9.0.1 Safari/601.2.7'}, cookies=cookies_for_login, allow_redirects=True)
r2
r2.text
out = open('/Users/john/Desktop/out2.html', 'w')
out.write(r2.text)
out.close()
login_params
register_params = {
    'first_name': 'John',
    'last_name': 'Smith',
    'email_address': 'jm2@lonepixel.com',
    'password': 'test12',
    'confirmPassword': 'test12',
    'organization_name': 'HW1',
    'organization_type': '42',
    'user_role': '14',
    'subject_area': ['5', '6'],
    'subject_areas': '5,6',
    'have_read_user_agreement': 'true',
    'registerButton': 'Register',
    'reg_type': 'Guest',
    'http_method_name': 'POST',
    'opaque_info_name': 'This is opaque info',
    'opaque_info_value': 'This is opaque info',
    'anon_type': 'ANON_GUEST',
}
cookies
init_cookies_response = requests.get(init_cookies_url, headers=init_cookie_headers, allow_redirects=False)
init_cookies_response
init_cookies_response.cookies
cookies_from_init_cookies = dict(init_cookies_response.cookies)
cookies_from_init_cookies
register_response = requests.post(register_url, data=register_params, cookies=cookies_from_init_cookies, allow_redirects=False)
register_response
register_response.text
register_response.cookies
dict(register_response.cookies)
'aws' in register_response.text
'acw' in register_response.text
utt = '8767a73967cf051f8001ab2-831d8551083693a2-J0'
acw = '7767a73967cf051f8001ab2-831d8551083693a2-1Hp%7C%24%7Cgy8su75uZX6P46jm1vkkhyAREzncQinXCqC%2B9u%2Ftw4J2DNTWEteGoxm67Jsh44K6go%2Bmh1JYdy22GJeiPfu1pgAVFG1Tz9IONuJoCNjYEkA%3D'
out = open('/Users/john/Desktop/out3.html', 'w')
out.write(register_response.text)
out.close()
ra1 = requests.get('//acw.sciencedirect.com/SSOCore/update?acw=7767a73967cf051f8001ab2-831d8551083693a2-1Hp%7C%24%7Cgy8su75uZX6P46jm1vkkhyAREzncQinXCqC%2B9u%2Ftw4J2DNTWEteGoxm67Jsh44K6go%2Bmh1JYdy22GJeiPfu1pgAVFG1Tz9IONuJoCNjYEkA%3D&utt=8767a73967cf051f8001ab2-831d8551083693a2-J0', cookies=dict(register_response.cookies), allow_redirects=False)
ra1 = requests.get('http://acw.sciencedirect.com/SSOCore/update?acw=7767a73967cf051f8001ab2-831d8551083693a2-1Hp%7C%24%7Cgy8su75uZX6P46jm1vkkhyAREzncQinXCqC%2B9u%2Ftw4J2DNTWEteGoxm67Jsh44K6go%2Bmh1JYdy22GJeiPfu1pgAVFG1Tz9IONuJoCNjYEkA%3D&utt=8767a73967cf051f8001ab2-831d8551083693a2-J0', cookies=dict(register_response.cookies), allow_redirects=False)
ra1
ra1.text
ra1.cookies
ra1 = requests.get('http://acw.scopus.com/SSOCore/update?acw=7767a73967cf051f8001ab2-831d8551083693a2-1Hp%7C%24%7Cgy8su75uZX6P46jm1vkkhyAREzncQinXCqC%2B9u%2Ftw4J2DNTWEteGoxm67Jsh44K6go%2Bmh1JYdy22GJeiPfu1pgAVFG1Tz9IONuJoCNjYEkA%3D&utt=8767a73967cf051f8001ab2-831d8551083693a2-J0', cookies=dict(register_response.cookies), allow_redirects=False)
ra1
ra1 = requests.get('http://acw.sciverse.com/SSOCore/update?acw=7767a73967cf051f8001ab2-831d8551083693a2-1Hp%7C%24%7Cgy8su75uZX6P46jm1vkkhyAREzncQinXCqC%2B9u%2Ftw4J2DNTWEteGoxm67Jsh44K6go%2Bmh1JYdy22GJeiPfu1pgAVFG1Tz9IONuJoCNjYEkA%3D&utt=8767a73967cf051f8001ab2-831d8551083693a2-J0', cookies=dict(register_response.cookies), allow_redirects=False)
ra1
ra1 = requests.get('http://acw.elsevier.com/SSOCore/update?acw=7767a73967cf051f8001ab2-831d8551083693a2-1Hp%7C%24%7Cgy8su75uZX6P46jm1vkkhyAREzncQinXCqC%2B9u%2Ftw4J2DNTWEteGoxm67Jsh44K6go%2Bmh1JYdy22GJeiPfu1pgAVFG1Tz9IONuJoCNjYEkA%3D&utt=8767a73967cf051f8001ab2-831d8551083693a2-J0', cookies=dict(register_response.cookies), allow_redirects=False)
ra1
switch_to_registered_user_params = {
    'submit': 'Continue',
    "auth_type": "SWITCH_TO_REGISTERED_USER",
    "auth_token": "6767a73967cf051f8001ab2-831d8551083693a2-Fe",
    "username": "jm2@lonepixel.com",
    "encrypted_password": "00650076004C004C0077006D00530052005800320051003D",
    "http_method_name": "GET",
}
register_url
ra1 = requests.get('https://www.developers.elsevier.com/action/customer/authenticate', params=switch_to_registered_user_params, cookies=dict(register_response.cookies), allow_redirects=False)
ra1
ra1.cookies
dict(ra1.cookies)
dict(ra1.headers)
switch_to_registered_user_params
cookies_for_switch = dict(register_cookies)
cookies_for_switch
cookies_for_switch['acw'] = acw
cookies_for_switch['utt'] = utt
cookies_for_switch['JSESSIONID'] = cookies_for_switch['SESSIONID_COOKIE']
ra1 = requests.get('https://www.developers.elsevier.com/action/customer/authenticate', params=switch_to_registered_user_params, cookies=cookies_for_switch, allow_redirects=False)
ra1 = requests.get('https://www.developers.elsevier.com/action/customer/authenticate', params=switch_to_registered_user_params, cookies=cookies_for_switch, allow_redirects=False)
ra1
ra1.cookies
dict(ra1.headers)
ra1.url
cookies_for_switch
headers_for_switch = {
'Referer': 'https://www.developers.elsevier.com/action/customer/profile',
'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.7 (KHTML, like Gecko) Version/9.0.1 Safari/601.2.7'
}
ra2 = requests.get('https://www.developers.elsevier.com/action/customer/authenticate', params=switch_to_registered_user_params, cookies=dict(register_response.cookies), allow_redirects=False)
ra2
ra2.text
ra2.headers
ra1 = requests.get('https://acw.sciverse.com/SSOCore/update?acw=7767a73967cf051f8001ab2-831d8551083693a2-1Hp%7C%24%7Cgy8su75uZX6P46jm1vkkhyAREzncQinXCqC%2B9u%2Ftw4J2DNTWEteGoxm67Jsh44K6go%2Bmh1JYdy22GJeiPfu1pgAVFG1Tz9IONuJoCNjYEkA%3D&utt=8767a73967cf051f8001ab2-831d8551083693a2-J0', cookies=dict(register_response.cookies), allow_redirects=False)
ra1
ra1.cookies
init_cookies_url
init_cookies_response = requests.get(init_cookies_url, headers=init_cookie_headers, allow_redirects=False)
init_cookies_response
init_cookies_response.cookies
init_cookie_headers
init_cookies_response.text
init_cookies_url
init_cookies_response = requests.get(init_cookies_url, headers=init_cookie_headers, allow_redirects=False)
init_cookies_response
