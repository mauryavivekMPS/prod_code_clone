import json
import logging
import os
import re
import requests
import threading
import time
from email.utils import parsedate_tz, mktime_tz
from flask import Flask, request, jsonify
from functools import wraps
from logging.handlers import TimedRotatingFileHandler

app = Flask("rate_limiter")

# https://github.com/pallets/flask/issues/2549
# fixes:
# File "/usr/local/lib/python3.5/site-packages/flask/json.py", line 251, in jsonify
#    if current_app.config['JSONIFY_PRETTYPRINT_REGULAR'] and not request.is_xhr:
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

logging.basicConfig(
    datefmt='%d/%b/%Y %H:%M:%S',
    format='[%(asctime)s.%(msecs)03d] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
    handlers=[TimedRotatingFileHandler(os.path.join(os.environ.get('IVRATELIMITER_LOG_DIR', '/var/log/ivratelimiter/'), 'api.log'), when='D', interval=1)],
    level=logging.WARNING
)

log = logging.getLogger(__name__)

# blocked_until records a hard block on requests for a specified backend until
# the unix time value has passed
blocked_until = {
    'crossref': 0,
    'pubmed': 0,
}

# per_second_limit imposes a rate limit on requests to the specified backend
per_second_limit = {
    'crossref': 50.0,
    'pubmed': 9.0,
}

# rate_limit_mu locks access to blocked_until and per_second_limit
rate_limit_mu = threading.Lock()


# user-agent value to identify contact point for impactvizor related traffic to
# crossref
crossref_user_agent = os.environ.get('IVETL_CROSSREF_USER_AGENT', 'impactvizor-pipeline/1.0 (mailto:vizor-support@highwirepress.com)')

def max_per_second(backend, limit=1):
    """ max_per_second returns the max requests per second for a backend (e.g.,
    crossref or pubmed) if it is defined in per_sec_limit, otherwise it
    returns limit. """

    global rate_limit_mu
    global per_second_limit
    with rate_limit_mu:
        if backend in per_second_limit.keys():
            limit = per_second_limit[backend]
        else:
            log.warning("no per_second_limit key set for backend %s" % (backend))

    return limit

def blocked_wait(backend):
    """ if blocked_until[backend] in the future, sleep until past that unix time. """

    now = time.time()
    until = now

    global rate_limit_mu
    global blocked_until
    with rate_limit_mu:
        if backend in blocked_until.keys():
            until = blocked_until[backend]
        else:
            log.warning("no blocked_until key set for backend %s" % (backend))

    if until > now:
      seconds = (1 + until - now)
      log.debug("blocked_wait sleeping for %d seconds" % seconds)
      time.sleep(seconds)


def check_retry_after(backend, response):
    """ If an http status 429 Too Many Requests or 503 Service Unavailable is
    returned in a response for the backend (e.g., crossref or pubmed), look for
    a Retry-After header and use that to set retry_after, otherwise default to
    five minutes in the future. """

    if response is None:
        log.warning("check_retry_after response is not set")
        return
    if not hasattr(response, 'status_code'):
        log.warning("check_retry_after response.status_code not set")
        return

    retry_after = 0
    if "Retry-After" in response.headers:
        retry_after_str = response.headers['Retry-After']

        if re.match(r"^\d+$", retry_after_str):
            retry_after = time.time() + int(retry_after_str)
        else:
            tparts = parsedate_tz(retry_after_str)
            if tparts is not None:
                retry_after = mktime_tz(tparts)
            else:
                log.warning("unable to parse Retry-After header, defaulting to 300 seconds in the future: %s" % (retry_after_str))
                retry_after = time.time() + 300

    if retry_after != 0:
        global rate_limit_mu
        global blocked_until
        with rate_limit_mu:
            blocked_until[backend] = retry_after
            log.debug("set blocked_until[%s] to %s" % (backend, retry_after))


def set_crossref_advisory_limit(response):
    """ sets the per-second rate limit for crossref requests

    This function sets a limit of (limit/interval) for a given set of crossref
    X-Rate-Limit-Limit and X-Rate-Limit-Interval header values, where interval
    is always a value in seconds.

    It defaults to 50 requests per second if the header values are not sent by
    crossref.
    """

    # set default of 50 requests per 1 second unless overridden by headers
    # Crossref says they will be sending
    backend = 'crossref'
    x_limit = 50
    x_interval = 1

    if response is None:
        log.warning("set_crossref_advisory_limit response is not set")
        return
    if not hasattr(response, 'status_code'):
        log.warning("set_crossref_advisory_limit response.status_code not set")
        return
    if not hasattr(response, 'url'):
        log.warning("set_crossref_advisory_limit response.url not set")
        return
    if not hasattr(response, 'headers'):
        log.warning("set_crossref_advisory_limit response.headers not set")
        return

    # crossref says they will always send X-Rate-Limit-Limit and
    # X-Rate-Limit_Interval headers
    try:
        x_limit = float(response.headers['X-Rate-Limit-Limit'])
        log.debug("X-Rate-Limit-Limit: %d" % x_limit)
    except KeyError:
        log.warning("X-Rate-Limit-Limit not set for request %s" % response.url)
    except ValueError:
        log.warning("X-Rate-Limit-Limit header was not numeric: %s" % response.headers['X-Rate-Limit-Limit'])

    try:
        x_interval = int(response.headers['X-Rate-Limit-Interval'].replace("s", ""))
        log.debug("X-Rate-Limit-Interval: %d" % x_interval)
    except KeyError:
        log.warning("X-Rate-Limit-Interval not returned for request %s" % response.url)
    except ValueError:
        log.warning("X-Rate-Limit-Interval header was not numeric: %s" % response.headers['X-Rate-Limit-Interval'])

    # compute our per-second limit, either using the initial defaults whatever
    # per-second limit Crossref specified
    limit = float((x_limit / float(x_interval)))
    log.debug("computed crossref limit: %d" % limit)

    # if necessary update the global per_second_limit
    global rate_limit_mu
    global per_second_limit
    with rate_limit_mu:
        if not hasattr(per_second_limit, backend) or per_second_limit[backend] != limit:
            log.info("setting per_second_limit[%s] to %d" % (backend, limit))
            per_second_limit[backend] = limit


def rate_limited(backend):
    """ rate_limited rate limits calls to a function to a maximum number per second

    The backend passed in identifies the backend in flight, e.g., crossref or pubmed. """
    lock = threading.Lock()

    def decorate(func):
        last_time_called = time.time()

        @wraps(func)
        def rate_limited_function(*args, **kwargs):
            nonlocal last_time_called

            # blocked_wait will sleep if we're still within the window of time
            # that a backend requested we wait until before making more
            # requests (the retry-after header value they sent, or a default of
            # 300 seconds).
            blocked_wait(backend)

            # limit returns the number of requests per second allowed by the
            # backend (e.g., crossref or pubmed)
            limit = max_per_second(backend)
            if limit <= 0:
                # invalid limit returned, set the limit to 1 request per minute
                log.error("max_per_second(%s) returned a value <= 0: %f" % (backend, float(limit)))
                limit = float(0.01666666666666666666)

            min_interval = 1.0 / float(limit)

            green_light = False
            while not green_light:

                with lock:
                    elapsed = time.time() - last_time_called
                    left_to_wait = min_interval - elapsed
                    if left_to_wait <= 0:
                        green_light = True
                        last_time_called = time.time()

                if left_to_wait > 0:
                    time.sleep(left_to_wait)

            return func(*args, **kwargs)

        return rate_limited_function

    return decorate


@rate_limited('crossref')
def do_crossref_request(url, timeout=120):
    headers = {
        'User-Agent': crossref_user_agent
    }
    log.info('Requested crossref: %s' % url)
    response = requests.get(url, headers=headers, timeout=timeout)
    check_retry_after('crossref', response)
    set_crossref_advisory_limit(response)

    return response

@rate_limited('pubmed')
def do_pubmed_request(url, timeout=120):
    log.info('Requested pubmed: %s' % url)
    response = requests.get(url, timeout=timeout)
    check_retry_after('pubmed', response)

    return response

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
    #     'timeout': 120,
    # }

    service = ''
    url = ''

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
    except json.decoder.JSONDecodeError:
        log.warning('unable to decode request body as json', exc_info=True)
        wrapped_response = {
            'limit_status': 'error',
        }
    except Exception:
        log.warning('Unexpected exception on: (%s, %s)' % (service, url), exc_info=True)
        wrapped_response = {
            'limit_status': 'error',
        }

    return jsonify(wrapped_response), 200
