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

# inflight_count tracks the number of in-flight requests for a given backend
inflight_count = {
    'crossref': 0,
    'pubmed': 0,
}

# rate_limit_mu locks access to blocked_until, per_second_limit, and inflight_count
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
            limit = float(per_second_limit[backend])
        else:
            log.warning("no per_second_limit set for backend %s, defaulting to 1" % (backend))
            limit = 1.0

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
            log.warning("no blocked_until[%s] key set" % (backend))

    if until > now:
      seconds = (1 + until - now)
      log.debug("blocked_wait[%s] sleeping for %d seconds" % (backend, seconds))
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

        if re.match(r"^\s*\d+\s*$", retry_after_str):
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
        log.info("X-Rate-Limit-Limit not set for request %s" % response.url)
    except ValueError:
        log.warning("X-Rate-Limit-Limit header was not numeric: %s" % response.headers['X-Rate-Limit-Limit'])

    try:
        x_interval = int(response.headers['X-Rate-Limit-Interval'].replace("s", ""))
        log.debug("X-Rate-Limit-Interval: %d" % x_interval)
    except KeyError:
        log.info("X-Rate-Limit-Interval not returned for request %s" % response.url)
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

    # lock is shared between threads for this backend
    lock = threading.Lock()

    # decorate implements the rate limiting logic for restricting the request
    # rate to func, which we expect to return an http response
    def decorate(func):
        # last_time_called will track the last time we allowed a new http
        # request to be issued for this backend
        last_time_called = time.time()

        @wraps(func)
        def rate_limited_function(*args, **kwargs):

            # blocked_wait will sleep if we're still within the window of time
            # that a backend requested we wait before we try again.
            blocked_wait(backend)

            # green_light is initially False and will be set to True if the
            # number of inflight requests does not exceed a limit, and if the
            # amount of time elapsed since the last request is large enough to
            # not exceed the maximum requests per second allowed for the
            # backend
            green_light = False

            while not green_light:
                with lock:
                    # last_time_called, scoped above, tracks the last time we
                    # allowed this wrapper method to proceed with issuing a new
                    # request
                    nonlocal last_time_called

                    # max_per_sec is the maximum number of requests we are
                    # allowed to issue per second, it is possible for this to
                    # be a fractional number between 0.0 and 0.9 if the limit
                    # is lower than one request per second.
                    max_per_sec = max_per_second(backend)

                    # min_interval is the time we need to wait in-between new
                    # requests to not exceed max_per_sec
                    min_interval = 1.0 / max_per_sec;

                    # compute the elapsed time since our last new request
                    now = time.time()
                    elapsed = now - last_time_called

                    # time left to wait before we may issue a new request, this
                    # may be negative if we're already waited long enough
                    left_to_wait = min_interval - elapsed

                    # record the number of inflight requests open right now
                    with rate_limit_mu:
                        inflight = inflight_count[backend]

                    # if the inflight request count is lower than the
                    # max_per_sec limit and we've waited long enough since our
                    # last new request, give the green light to proceed.
                    if inflight < max_per_sec and left_to_wait <= 0:
                        last_time_called = now
                        green_light = True

                # if left_to_wait is positive, we need to sleep for that value
                # before we check again
                if left_to_wait > 0:
                    time.sleep(left_to_wait)

            # we've been given the green light to proceed, so increment our
            # inflight counter just before we execute our request to the
            # backend
            with rate_limit_mu:
                inflight_count[backend] += 1
                log.debug("+ inflight_count[%s]: %d" % (backend, inflight_count[backend]))

            try:
                # issue a request to the backend and record the response
                response = func(*args, **kwargs)
            finally:
                # once a response has been returned, or has failed, decrement
                # our inflight counter
                with rate_limit_mu:
                    inflight_count[backend] -= 1
                    log.debug("+ inflight_count[%s]: %d" % (backend, inflight_count[backend]))

            # return the response from the backend
            return response

        return rate_limited_function

    return decorate


@rate_limited('crossref')
def do_crossref_request(url, timeout=120):
    backend = 'crossref'
    log.info('Requested %s: %s' % (backend, url))

    headers = {
        'User-Agent': crossref_user_agent
    }
    response = requests.get(url, headers=headers, timeout=timeout)

    check_retry_after('crossref', response)
    set_crossref_advisory_limit(response)

    return response

@rate_limited('pubmed')
def do_pubmed_request(url, timeout=120):
    backend = 'pubmed'
    log.info('Requested %s: %s' % (backend, url))

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
