This directory holds the files used to build the ivratelimiter_test container.

To run a test launch your impactvizor environment and run the
ivratelimiter_test container inside the same network.  For example:

  docker run --rm --network iv_default fr-harbor.highwire.org/impactvizor/ivratelimiter_test:latest

The ivratelimiter service that we are testing accepts a JSON body that defines
a service name and a URL to request.  For each request that arrives it computes
whether or not it needs to sleep for some period of time before allowing the
request to run.

Once the timer for a request has elapsed, the request is sent to the backend
service (e.g., to a service such as crossref or pubmed).  The ivratelimiter
service allows for each service point to define its own limits.  Currently we
have two services set up:

- crossref: crossref sends headers to indicate the desired rate limit, and
  ivratelimiter processes those headers to dynamically adjust its rate limit

- pubmed: pubmed is configured with a static 9 requests/sec limit.

By default the container will run ivratelimiter_test.sh from inside the
container, and it will assume it needs to connect to ratelimiter:8082, and
that requests back to the test service should come to the container ip on port
8080.  The defaults can be overridden using the -f <host>:<port> flag to
override the frontend (the ivratelimiter service address) and the -b
<host>:<port> flag (the backend service hosting ivratelimiter_httpd).

The test script handles the startup and shutdown of the ivratelimiter_httpd
daemon, and sets the contents of the http response based on the type of test
(crossref or pubmed).  Once ivratelimiter_httpd is running, the script uses GNU
Parallel to send a large number of requests in parallel to the ivratelimiter
server.

The ivratelimiter server is expected to gate the requests it then sends back to
the ivratelmiter_httpd server.  The test script examines the requests per
second logged by ivratelmiter_httpd to determine success or failure of a test.
If the requests per second exceeds expected rates, a failure is logged.

After the requests per seconds are run, a set of retry-after tests are run.
With these tests the ivratelimiter_httpd server is set up to return an error
status with a Retry-After header, indicating that the client should back off
from making further requests for some specified period of time.  The test
script checks that ivratelimiter obeys such directives.

Probably this could be rewritten as a standalone python program, to eliminate
the dependency on Go and Unix tooling.
