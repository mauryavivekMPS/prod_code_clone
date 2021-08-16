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

class Counter:
    """ Counter tracks the number of requests made per second for some number
    of seconds into the past.  It uses Unix Epoch time to track seconds.  """

    def __init__(self, limit=1, track_active=False):
        """ initialize a new Counter, optionally specifying the number of
        seconds into the past to track.  If no limit is specified the default
        is 1. If track_active=True is passed in then inc/dec will track active
        in-flight requests (meant to be used for sites that are actually rate
        limiting based on in-flight requests instead of requests arriving per
        second). """
        self.t = [0]*limit
        self.n = [0]*limit

        self.track_active = track_active
        if self.track_active:
            self.active = 0
        else:
            self.active = -1

    def inc(self, n=1):
        """ inc increments the counter for the current second in time by n.  If
        n is not specified the default is 1.  The resulting incremented counter
        value is returned. """
        t = int(time.time())
        if (t != self.t[-1]):
            self.t = self.t[1:] + [t]
            self.n = self.n[1:] + [n]
        else:
            self.n[-1] += n;

        if self.track_active:
            self.active += n

        return self.n[-1]

    def dec(self, n=1):
        """ dec decements the active in-flight counter by n if the Counter was
        initialized with track_active=True, otherwise it is a no-op.  If n is
        not specified the default is 1. """
        if self.track_active:
            self.active -= n

    def cur(self):
        """ cur returns the counter for the current second in time. """
        t = int(time.time())
        if (t == self.t[-1]):
            return self.n[-1]
        else:
            return 0

    def tracked_active(self):
        """ tracked_active returns the current active in-flight counter value,
        if the value is -1 it means the Counter was not initialized with
        track_active=True and the Counter is not tracking active counts when
        inc/dec are called. """
        return self.active

    def all(self):
        """ all returns a dictionary mapping the most recent counter
        seconds to their counter values. """
        return {self.t[i]: self.n[i] for i in range(len(self.t))}

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
    level=logging.DEBUG
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

# override_per_second_limit is consulted to specify a lower limit than
# might otherwise exist in per_second_limit.
override_per_second_limit = {
#  'crossref': 40.0,
}

# counters tracks the number of requests dispatched to a given backend for a
# limited span of seconds into the past
counters = {
    'crossref': Counter(1, track_active=True),
    'pubmed': Counter(1),
}

# rate_limit_mu locks access to blocked_until, per_second_limit, and counters
rate_limit_mu = threading.Lock()


# user-agent value to identify contact point for impactvizor related traffic to
# crossref
crossref_user_agent = os.environ.get('IVETL_CROSSREF_USER_AGENT', 'impactvizor-pipeline/1.0 (mailto:vizor-support@highwirepress.com)')

def max_per_second(backend, limit=1):
    """ max_per_second returns the max requests per second for a backend (e.g.,
    crossref or pubmed) if it is defined in per_sec_limit, otherwise it returns
    limit, which has a default value of 1.0 if not specified by the caller. """

    global rate_limit_mu
    global per_second_limit
    with rate_limit_mu:
        if backend in per_second_limit.keys():
            limit = float(per_second_limit[backend])
            if backend in override_per_second_limit.keys():
                override = float(override_per_second_limit[backend])
                if limit > override:
                    log.debug("overriding per_second_limit for backend %s: %0.3f -> %0.3f" % (backend, limit, override))
                    limit = override
        else:
            log.warning("no per_second_limit set for backend %s, defaulting to %0.3f" % (backend, limit))

    return limit

def blocked_wait(backend):
    """ if blocked_until[backend] is in the future, sleep until past that unix time. """

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
    """ Check for a Retry-After header and use that to set retry_after.  If a
    Retry-After is specified but could not be parsed, a default of 300 seconds
    into the future is used. """

    if response is None:
        log.warning("check_retry_after response is not set")
        return
    if not hasattr(response, 'status_code'):
        log.warning("check_retry_after response.status_code not set")
        return

    retry_after = 0
    if "Retry-After" in response.headers:
        retry_after_str = response.headers['Retry-After']

        # if Retry-After is a single digit, assume it is seconds
        if re.match(r"^\s*\d+\s*$", retry_after_str):
            retry_after = time.time() + int(retry_after_str)
        else:
            # otherwise if Retry-After is an RFC 1123 compatible date string,
            # parse it
            tparts = parsedate_tz(retry_after_str)
            if tparts is not None:
                retry_after = mktime_tz(tparts)
            else:
                # unable to determine the time, assume 5 minutes into the
                # future
                log.warning("unable to parse Retry-After header, defaulting to 300 seconds in the future: %s" % (retry_after_str))
                retry_after = time.time() + 300

    if retry_after != 0:
        global rate_limit_mu
        global blocked_until
        with rate_limit_mu:
            blocked_until[backend] = retry_after
            log.debug("set blocked_until[%s] to %s" % (backend, retry_after))


def set_crossref_advisory_limit(response, backend):
    """ Set the per-second rate limit for crossref requests.

    This function sets a limit of (limit/interval) for a given set of crossref
    X-Rate-Limit-Limit and X-Rate-Limit-Interval header values, where interval
    is always a value in seconds.

    It defaults to 50 requests/second if the header values are not set.  """

    # set default of 50 requests per 1 second unless overridden by headers
    # Crossref says they will be sending
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
    """ Rate limit calls to a function to a maximum number per second.

    The backend identifies the target, e.g., crossref or pubmed. """

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
                    # may be negative if we have already waited long enough
                    left_to_wait = min_interval - elapsed

                    # if we've waited long enough since our last new request,
                    # and if the current dispatched request count is lower than
                    # the max_per_sec limit, give the green light to proceed.
                    if left_to_wait <= 0:
                        with rate_limit_mu:
                            counter = counters[backend]
                            active = counter.tracked_active()
                            dispatched = counter.cur()
                        if active > -1:
                            log.debug("%s: active: %d, dispatched: %d" % (backend, active, dispatched))
                        else:
                            log.debug("%s: dispatched: %d" % (backend, dispatched))

                        # if active is not -1 it indicates we are tracking
                        # active (in-flight) requests for this backend,  we
                        # need to compare it to max_per_sec and treat it as the
                        # in-flight maximum. If we've reached the in-flight
                        # maximum, we need to wait until a slot is freed up.
                        #
                        # Otherwise check how many requests we've dispatched in
                        # the current second, and if that's reached max_per_sec
                        # we likewise need to sleep.
                        #
                        # If neither condition applies we may proceed to send
                        # the request.
                        if active >= max_per_sec:
                            left_to_wait = 0.250
                        elif dispatched >= max_per_sec:
                            left_to_wait = 0.250
                        else:
                            last_time_called = now
                            green_light = True

                # if left_to_wait is positive, we need to sleep for that value
                # before we check again
                if left_to_wait > 0:
                    time.sleep(left_to_wait)

            # we've been given the green light to proceed, so increment our
            # dispatched counter just before we execute our request to the
            # backend
            try:
                with rate_limit_mu:
                    counters[backend].inc(1)

                # issue a request to the backend and record the response
                response = func(*args, **kwargs)
            finally:
                with rate_limit_mu:
                    counters[backend].dec(1)

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
    set_crossref_advisory_limit(response, backend)

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
                'url': url,
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
