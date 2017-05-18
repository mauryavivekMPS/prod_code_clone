import time
import threading
import requests
import logging
import traceback
from functools import wraps
from flask import Flask, request, jsonify

app = Flask("rate_limiter")

logging.basicConfig(
    filename='/var/log/ivratelimiter/api.log',
    format='[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
    datefmt='%d/%b/%Y %H:%M:%S',
    # format='%(message)s',
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
            # log.info('%s acquiring lock' % threading.get_ident())
            lock.acquire()
            # log.info('%s got lock' % threading.get_ident())
            nonlocal last_time_called
            elapsed = time.perf_counter() - last_time_called
            left_to_wait = min_interval - elapsed

            if left_to_wait > 0:
                # log.info('% sleep for %s' % (threading.get_ident(), left_to_wait))
                time.sleep(left_to_wait)

            ret = func(*args, **kwargs)
            last_time_called = time.perf_counter()
            # log.info('%s releasing lock' % threading.get_ident())
            lock.release()
            # log.info('%s released' % threading.get_ident())
            return ret

        return rate_limited_function

    return decorate


@rate_limited(4)
def do_crossref_request(url):
    # log.info('Requested crossref: %s' % url)
    # log.info('%s requested crossref: %s' % (threading.get_ident(), url))
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

    url = ''

    try:
        request_type = request.json['type']
        service = request.json['service']
        url = request.json['url']

        # log.info('Queued %s: %s' % (service, url))
        # log.info('%s queued %s: %s' % (threading.get_ident(), service, url))

        if request_type == 'GET':
            service_response = SERVICES[service](url)
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
        log.info('Unexpected exception on: (%s, %s)' % (service, url))
        log.info(traceback.format_exc())
        wrapped_response = {
            'limit_status': 'error',
        }

    return jsonify(wrapped_response), 200
