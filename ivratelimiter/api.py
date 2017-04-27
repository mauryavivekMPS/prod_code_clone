import time
import threading
import requests
import logging
from functools import wraps
from flask import Flask, request, jsonify

app = Flask("rate_limiter")

logging.basicConfig(
    filename='/var/log/ivratelimiter/api.log',
    format='[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
    datefmt='%d/%b/%Y %H:%M:%S',
    level=logging.INFO
)

log = logging.getLogger(__name__)


def rate_limited(max_per_second):
    lock = threading.Lock()
    min_interval = 1.0 / max_per_second

    def decorate(func):
        last_time_called = time.perf_counter()

        @wraps(func)
        def rate_limited_function(*args, **kwargs):
            lock.acquire()
            nonlocal last_time_called
            elapsed = time.perf_counter() - last_time_called
            left_to_wait = min_interval - elapsed

            if left_to_wait > 0:
                time.sleep(left_to_wait)

            ret = func(*args, **kwargs)
            last_time_called = time.perf_counter()
            lock.release()
            return ret

        return rate_limited_function

    return decorate


# @rate_limited(18)
def do_crossref_request(url):
    log.info('requested crossref: %s' % url)
    return requests.get(url, timeout=30)


SERVICES = {
    'crossref': do_crossref_request,
}


@app.route('/limit', methods=['POST'])
def limit():

    # example_request = {
    #     'type': 'GET',
    #     'service': 'crossref',
    #     'url': 'http://api.foo.com/?a=1&b=4',
    # }

    try:
        request_type = request.json['type']
        service = request.json['service']
        url = request.json['url']

        log.info('queued %s: %s' % (service, url))

        if request_type == 'GET':
            service_response = SERVICES[service](url)
            wrapped_response = {
                'limit_status': 'ok',
                'status_code': service_response.status_code,
                'text': service_response.text,
            }
        else:
            wrapped_response = {
                'limit_status': 'error',
            }
    except:
        wrapped_response = {
            'limit_status': 'error',
        }

    return jsonify(wrapped_response), 200
