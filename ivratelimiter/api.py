import os
import time
import threading
import requests
import logging
from functools import wraps
from flask import Flask, request, jsonify
from logging.handlers import TimedRotatingFileHandler

app = Flask("rate_limiter")

logging.basicConfig(
    datefmt='%d/%b/%Y %H:%M:%S',
    format='[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
    # NB: the logic around IVETL_WORKING_DIR here seems wrong, it will
    # put a file api.log under that dir if the env is defined
    handlers=[TimedRotatingFileHandler(os.path.join(os.environ.get('IVETL_WORKING_DIR', '/var/log/ivratelimiter/'), 'api.log'), when='D', interval=1)],
    level=logging.DEBUG
)

log = logging.getLogger(__name__)

# crossref_blocked_until imposes a hard block on requests until the unix time
# in this value has passed
crossref_blocked_until = 0

# crossref_per_second_limit imposes a rate limit on requests to crossref.org
crossref_per_second_limit = 49

# crossref_rate_limit_mu locks access to crossref_per_second_limit
# and crossref_blocked_until
crossref_rate_limit_mu = threading.Lock()


def crossref_blocked_wait():
    """ if crossref_blocked_until is set then sleep until that time has passed """
    global crossref_rate_limit_mu
    global crossref_blocked_until
    with crossref_rate_limit_mu:
        if crossref_blocked_until > 0:
            now = time.time()
            if crossref_blocked_until > now:
                time.sleep(1 + crossref_blocked_until - now)
            crossref_blocked_until = 0


def crossref_max_per_second():
    """ return a copy of the current crossref_per_second_limit rate """
    global crossref_rate_limit_mu
    global crossref_per_second_limit
    with crossref_rate_limit_mu:
        return crossref_per_second_limit


def set_crossref_advisory_limit(response):
    """ sets the per-second rate limit for crossref requests

    This function sets a limit of ((limit/interval)-1) for a given set of
    crossref X-Rate-Limit-Limit and X-Rate-Limit-Interval header values.

    It defaults to 49 requests per second if the header values are not
    sent by crossref.

    If an http status 429 code (Too Many Requests) is returned, look for
    a Retry-After header and use that to set
    """

    if response is None:
        log.debug("set_crossref_advisory_limit response is not set")
        return
    if not hasattr(response, 'url'):
        log.debug("set_crossref_advisory_limit response.url not set")
        return
    if not hasattr(response, 'headers'):
        log.debug("set_crossref_advisory_limit response.headers not set")
        return

    # check for a 429 status code
    retry_after = 0
    if response.status_code == 429:
        try:
            retry_after = 1 + time.time() + int(response.headers['Retry-After'])
            log.debug("Status 429 response blocking until %s (GMT)" %
                time.asctime(time.gmtime(retry_after)))
        except KeyError:
            retry_after = time.time() + 300
            log.debug("Status 429 response did not return a Retry-After, defaulting to 300 seconds")

    # default of 50 requests per 1 second, which
    # will become a limit of 49 requests/sec below
    x_limit = 50
    x_interval = 1

    # crossref says they will always send these headers
    try:
        x_limit = int(response.headers['X-Rate-Limit-Limit'])
        log.debug("X-Rate-Limit-Limit: %d" % x_limit)
    except KeyError:
        log.warning("X-Rate-Limit-Limit not set for request %s" % response.url)
    try:
        x_interval = int(response.headers['X-Rate-Limit-Interval'].replace("s", ""))
        log.debug("X-Rate-Limit-Interval: %d" % x_interval)
    except KeyError:
        log.warning("X-Rate-Limit-Interval not returned for request %s" % response.url)

    # compute our per-second limit
    limit = int((x_limit / x_interval) - 1)
    log.debug("computed crossref limit: %d" % limit)

    # if necessary update the global crossref_per_second_limit
    global crossref_rate_limit_mu
    global crossref_per_second_limit
    global crossref_blocked_until
    with crossref_rate_limit_mu:
        if crossref_per_second_limit != limit:
            log.info("setting crossref_per_second_limit to %d" % limit)
            crossref_per_second_limit = limit
        if retry_after != 0:
            crossref_blocked_until = retry_after


def rate_limited(if_blocked_fn, max_per_second_fn):
    """ rate_limited rate limits calls to a function to a maxmimum number per second

    the max_per_second_fn should return an int indicating the maximum number of
    requests per second for calling the decorated function
    """
    lock = threading.Lock()

    def decorate(func):
        last_time_called = time.perf_counter()

        @wraps(func)
        def rate_limited_function(*args, **kwargs):
            if_blocked_fn()

            nonlocal max_per_second_fn
            limit = max_per_second_fn()
            if limit < 1:
                log.warn("got back a limit < 1 (%d), using a min_interval of 1 second" % limit)
                min_interval = 1.0
            else:
                min_interval = 1.0 / float(limit)
                log.debug("rate_limited limit %d: min_interval: %f" % (limit, min_interval))

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
                    log.debug("rate_limited left_to_wait: %f" % left_to_wait)
                    time.sleep(left_to_wait)

            return func(*args, **kwargs)

        return rate_limited_function

    return decorate


@rate_limited(crossref_blocked_wait, crossref_max_per_second)
def do_crossref_request(url, timeout=120):
    headers = {
        'User-Agent': 'impactvizor-pipeline/1.0 (mailto:vizor-support@highwirepress.com)'
    }
    log.info('Requested crossref: %s' % url)
    response = requests.get(url, headers=headers, timeout=timeout)
    set_crossref_advisory_limit(response)

    return response


SERVICES = {
    'crossref': do_crossref_request,
}


@app.route('/limit', methods=['POST'])
def limit():

    # example_request = {
    #   "type": "GET",
    #   "service": "crossref",
    #   "url": "http://localhost:8123/",
    #   "timeout": 120
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

    except Exception:
        log.warning('Unexpected exception on: (%s, %s)' % (service, url), exc_info=True)
        wrapped_response = {
            'limit_status': 'error',
        }

    return jsonify(wrapped_response), 200
