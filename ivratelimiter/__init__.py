"""

The rate_limiter application acts as a non-transparent proxy that will gate
requests to an origin, limiting the number of requests per second to the
origin.

This module defines a Flask @app.route on the path /limit, allowing for the
POST of JSON object.  The JSON object may contain the following keys:

    service: identifier for the rate limit handler (e.g., 'crossref')

    type: the http method to use on the origin (e.g., 'GET')

    url: the origin url to request (e.g., 'http://api.crossref.com/...')

    timeout: the maximum number of seconds to wait for a response (e.g., 120)

The limit() method at the bottom of this module accepts this incoming JSON
object and routes it to the appropriate service handler using the SERVICES dict
to map the service id to a function that will actually perform request.

The service handler should be annotated with the @rate_limited method defining
implementations of if_blocked_fn and max_per_second_fn (see below for the
discussion of those).  The service handler will be passed a url 'larg', and may
be passed a timeout 'kwarg':

    @rate_limited(if_blocked_fn, max_per_second_fn)
    def service_request_fn(url, timeout=...):

the @rate_limited annotation wrap the service handler with a call to
rate_limited, where the implementation of the gating logic occurs.

The rate_limited function expects two functions as parameters:

    if_blocked_fn: this function should take appropriate action if we have
    received an indication that we've been blocked, for example if the origin
    returned HTTP Status 429 (Too Many Requests) w/ Retry-After, we'd want to
    block until that Retry-After time had elapsed.

    If there will never be a situation where a block or outage might occur,
    you can just use an empty function that returns immediately.

    max_per_second_fn: return a floating point number indicating the number of
    requests per second allowed by the origin.

An example_request:

POST /limit HTTP/1.0
Content-Type: application/json
Content-Length: 107

{
  "service": "crossref",
  "type": "GET",
  "url": "http://api.foo.com/?a=1&b=2,c=3",
  "timeout": 120
}

HTTP/1.1 200 OK
Server: gunicorn/19.7.1
Date: Wed, 23 Oct 2019 18:05:01 GMT
Connection: keep-alive
Content-Type: application/json
Content-Length: 94

{
  "limit_status": "ok",
  "status_code": 200,
  "text": "{ \"a\":1, \"b\":2, \"c\":3 }"
}

"""
