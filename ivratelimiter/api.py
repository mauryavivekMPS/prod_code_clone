import os
import time
import threading
import requests
import logging
from functools import wraps
from flask import Flask, request, jsonify

app = Flask("rate_limiter")

# https://github.com/pallets/flask/issues/2549
# fixes:
# File "/usr/local/lib/python3.5/site-packages/flask/json.py", line 251, in jsonify
#    if current_app.config['JSONIFY_PRETTYPRINT_REGULAR'] and not request.is_xhr:
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

logging.basicConfig(
    filename=os.path.join( os.environ.get('IVETL_WORKING_DIR', '/var/log/ivratelimiter/'), 'api.log'),
    format='[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
    datefmt='%d/%b/%Y %H:%M:%S',
    # format='%(message)s',
    level=logging.WARNING
)

log = logging.getLogger(__name__)

crossref_user_agent = os.environ.get('IVETL_CROSSREF_USER_AGENT', 'impactvizor-pipeline/1.0 (mailto:vizor-support@highwirepress.com)')

def rate_limited(max_per_second):
    lock = threading.Lock()
    min_interval = 1.0 / max_per_second

    def decorate(func):
        last_time_called = time.perf_counter()

        @wraps(func)
        def rate_limited_function(*args, **kwargs):

            green_light = False
            while not green_light:

                with lock:
                    nonlocal last_time_called
                    elapsed = time.perf_counter() - last_time_called
                    left_to_wait = min_interval - elapsed
                    if left_to_wait <= 0:
                        last_time_called = time.perf_counter()
                        green_light = True

                if left_to_wait > 0:
                    time.sleep(left_to_wait)

            return func(*args, **kwargs)

        return rate_limited_function

    return decorate


@rate_limited(50)
def do_crossref_request(url, timeout=120):
    headers = {
        'User-Agent': crossref_user_agent
    }
    log.info('Requested crossref: %s' % url)
    return requests.get(url, headers=headers, timeout=timeout)

@rate_limited(9)
def do_pubmed_request(url, timeout=120):
    return requests.get(url, timeout=timeout)

SERVICES = {
    'crossref': do_crossref_request,
    'pubmed': do_pubmed_request
}

@app.route('/limit', methods=['POST'])
def limit():

    # example_request = {
    #     'type': 'GET',
    #     'service': 'crossref',
    #     'url': 'http://api.foo.com/?a=1&b=4',
    # }

    url = ''
    service = ''

    try:
        request_type = request.json['type']
        service = request.json['service']
        url = request.json['url']
        try:
            timeout = request.json['timeout']
        except KeyError:
            timeout = 120

        log.info('Queued %s: %s' % (service, url))

        if request_type == 'GET':
            service_response = SERVICES[service](url, timeout=timeout)
            wrapped_response = {
                'limit_status': 'ok',
                'status_code': service_response.status_code,
                'text': service_response.text,
            }
        else:
            log.info('Only GET is supported for (%s, %s), returning an error response' % (service, url))
            wrapped_response = {
                'limit_status': 'error',
            }

    except:
        log.warning('Unexpected exception on: (%s, %s)' % (service, url), exc_info=True)
        wrapped_response = {
            'limit_status': 'error',
        }

    return jsonify(wrapped_response), 200
