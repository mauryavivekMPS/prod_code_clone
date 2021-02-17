#!/bin/bash

# id is this program
id=$(basename "${0}");

# dirname is the directory for this program
dirname=$(dirname "${0}");

# exit codes
EXIT_BAD_ID=1
EXIT_BAD_NUM=2
EXIT_BAD_JOBS=3
EXIT_SEND_REQUESTS_FAILED=4
EXIT_BAD_NREQ=5
EXIT_BAD_NJOBS=6
EXIT_BAD_LIMIT=7
EXIT_MKTEMP_FAILED=8
EXIT_SERVER_FAILED=9
EXIT_PUBMED_LIMIT_EXCEEDED=10
EXIT_BAD_NREQ=11
EXIT_BAD_NJOBS=12
EXIT_BAD_LIMIT=13
EXIT_BAD_INTERVAL=14
EXIT_MKTEMP_FAILED=15
EXIT_SERVER_FAILED=16
EXIT_CROSSREF_LIMIT_EXCEEDED=17
EXIT_RETRY_AFTER_ERR=18
EXIT_UNKNOWN_ID=19
EXIT_MISSING_ADDR=20

# pick up command line arguments
# -f host:port
#    frontend host:port for ivratelimiter server
# -b host:port
#    backend host:port for ivratelimiter backend target
while [ $# -gt 0 ]; do
	case "${1}" in
	-f)
		frontend_addr="${2}"
		shift;
		;;
	-b)
		backend_addr="${2}";
		shift;
		;;
	esac
	shift;
done

# if a frontend_addr was not specified, use ratelimiter:8082
if [ "${frontend_addr}" = "" ]; then
	frontend_addr="ratelimiter:8082";
fi

# if a backend_addr was not specified, use the host ip on port 8080
if [ "${backend_addr}" = "" ]; then
	backend_addr=$(hostname -i):8080;
fi

if ! echo "${frontend_addr} ${backend_addr}" | grep -q -E '[^:]+:[1-9][0-9]* [^:]+:[1-9][0-9]*'; then
	echo "usage: ivratelimiter_test.sh -f <host>:<port> [-b <host>:<port> ]";
	echo "parameters:"
	echo "  -f <host>:<port>";
	echo "    frontend host and port for the ivratelimiter instance";
	echo "  -b <host>:<port>";
	echo "    backend host and port of the ivratelimiter target";
	echo "e.g.,";
	echo "  ivratelimiter_test.sh -f localhost:8082";
	echo "  ivratelimiter_test.sh -f localhost:8082 -b 192.168.10.103:8080";
	exit "${EXIT_MISSING_ADDR}";
fi

# ivratelimiter_body holds json records that may be sent to ivratelimiter to
# execute a request.  The service field in the json controls the routing of the
# request within ivratelimiter, allowing for different rate limiter controls to
# be applied on a per-service basis.  The url that is queried is the ip address
# of ivratelimiter_httpd
declare -A ivratelimiter_body
ivratelimiter_body[crossref]=$(printf '{
  "type":"GET",
  "service":"crossref",
  "url":"http://%s/",
  "timeout":120
}' "${backend_addr}");

ivratelimiter_body[pubmed]=$(printf '{
  "type":"GET",
  "service":"pubmed",
  "url":"http://%s/",
  "timeout":120
}' "${backend_addr}");

# shutdown <pid> [<logs>]
#
# shutdown kills <pid> if it is still active and removes any specified log
# files, and then clears the trap on EXIT
function shutdown () {
	server_pid="${1}";
	shift;

	if kill -0 "${server_pid}" 2>/dev/null; then
		kill "${server_pid}";
	fi

	if [ "$#" != 0 ]; then
		rm -f "${@}";
	fi

	# clear trap
	trap - INT;
	trap - EXIT;
}

# http_response <target> <status> <limit> <interval> <retry_after>
#
# http_response writes an http response body to <target>, using the specified
# <status>, which should consist of an http response code and optional response
# text.
#
# If <limit> and <interval> are defined and non-empty then X-Rate-Limit and
# X-Rate-Limit_Interval headers will be added to the response.
#
# If <retry_after> is defined and non-empty, then a Retry-After header will be
# added to the response.
function http_response () {
	local target;
	target="${1}";

	local status;
	status="${2}";

	local limit;
	limit="${3}";

	local interval;
	interval="${4}";

	local retry_after;
	retry_after="${5}";

	local tmp;
	if ! tmp=$(mktemp); then
		echo "${id}: unable to create temp response file";
		exit "${EXIT_MKTEMP_FAILED}";
	fi

	if [ "${status}" != "" ]; then
		printf "HTTP/1.1 %s\r\n" "${status}" > "${tmp}";
	else
		printf "HTTP/1.1 200 OK\r\n" > "${tmp}";
	fi

	if [ "${limit}" != "" ]; then
		printf "X-Rate-Limit-Limit: %s\r\n" "${limit}" >> "${tmp}";
	fi

	if [ "${interval}" != "" ]; then
		printf "X-Rate-Limit-Interval: %s\r\n" "${interval}" >> "${tmp}";
	fi

	if [ "${retry_after}" != "" ]; then
		printf "Retry-After: %s\r\n" "${retry_after}" >> "${tmp}";
	fi

	printf "\r\n" >> "${tmp}";

	mv "${tmp}" "${target}";
}

# launch_server <log> [<args>]
#
# launch_server runs ivratelimiter_httpd, logging to <log> and launching with any
# specified additional arguments.  On success the pid of the server is
# returned, otherwise an empty string is returned.
function launch_server () {
	local log
	log="${1}";
	shift;

	"${dirname}/ivratelimiter_httpd" "${@}" > "${log}" &
	local pid;
	pid="${!}";

	sleep 1;

	if kill -0 "${pid}"; then
		echo "${pid}";
	fi
}

# send_requests <id> <num> <jobs>
#
# send_requests sends <num> http requests for ivratelimiter_body[<id>] to
# ivratelimiter in parallel, up to <jobs> concurrent requests at a time.
function send_requests () {
	local backend;
	backend="${1}";

	local num;
	num="${2}";

	local jobs;
	jobs="${3}";

	local body;
	body=${ivratelimiter_body["${backend}"]};
	if [ "${body}" = "" ]; then
		echo "send_requests unable to resolve ivratelimiter_body for id: ${backend}" 1>&2;
		exit "${EXIT_BAD_ID}";_
	fi

	if [[ ! "${num}" =~ ^[1-9][0-9]* ]]; then
		echo "send_requests num not a postive integer: ${num}" 1>&2;
		exit "${EXIT_BAD_NUM}";
	fi

	if [[ ! "${jobs}" =~ ^[1-9][0-9]* ]]; then
			echo "send_requests jobs not a positive integer: ${jobs}" 1>&2;
			exit "${EXIT_BAD_JOBS}";
	fi

	# wait one full second before starting the test
	sleep 1;

	# make requests in parallel
	while IFS= read -r; do
		printf "curl -s -o /dev/null -X POST -H 'Content-Type: application/json' --data-binary '%s' http://%s/limit\0" "${body}" "${frontend_addr}";
	done < <(seq "${num}") | parallel -0 -P "${jobs}" --halt "now,fail=1" || exit "${EXIT_SEND_REQUESTS_FAILED}";
}

# test_ivratelimiter_pubmed <nreq> <njobs> <limit>
#
# Send <nreq> requests in parallel (up to <njobs>) to ivratelimiter using the
# pubmed workflow.  The <limit> needs to be the same value as is hardcoded in
# the ivratelimiter code for the pubmed workflow, as of this writing that is
# 9/1s.
function test_ivratelimiter_pubmed () {
	# nreq sets the number of requests to send through ivratelimiter
	local nreq;
	nreq="${1}";
	if [[ ! "${nreq}" =~ ^[1-9][0-9]* ]]; then
		echo "${id}: nreq must be a positive integer" 1>&2;
		exit "${EXIT_BAD_NREQ}";
	fi

	# njobs sets the number of parallel requests to submit to ivratelimiter
	local njobs;
	njobs="${2}";
	if [[ ! "${njobs}" =~ ^[1-9][0-9]* ]]; then
		echo "${id}: njobs must be a positive integer" 1>&2;
		exit "${EXIT_BAD_NJOBS}";
	fi

	# limit is the expected requests per second limit for pubmed
	local limit;
	limit="${3}";
	if [[ ! "${limit}" =~ ^[1-9][0-9]* ]]; then
		echo "${id}: limit must be a positive integer" 1>&2;
		exit "${EXIT_BAD_LIMIT}";
	fi
	
	# set up a temp file for the response body
	local rsp;
	if ! rsp=$(mktemp); then
		echo "${id}: unable to create temp response file";
		exit "${EXIT_MKTEMP_FAILED}";
	else
		# set up the http response body w/o any crossref headers
		http_response "${rsp}" "200 OK";
	fi
	
	# set up a temp file for the server log
	local log;
	if ! log=$(mktemp); then
		echo "${id}: unable to create temp access log";
		exit "${EXIT_MKTEMP_FAILED}";
	fi
	
	# launch ivratelimiter_httpd
	local server_pid;
	server_pid=$(launch_server "${log}" -a "${backend_addr}" -f "${rsp}");
	if [ "${server_pid}" = "" ]; then
		echo "${id}: unable to launch ivratelimiter_httpd test backend";
		exit "${EXIT_SERVER_FAILED}";
	fi

	# on exit shut down the fake http server and remove the logs
	trap 'shutdown "${server_pid}" "${rsp}" "${log}"' INT EXIT;
	
	# send the requests as limited by nreq and njobs.
	send_requests "pubmed" "${nreq}" "${njobs}";
	
	# compute the maximum requests per second rate that hit the fake server
	# after passing through ivratelimiter
	local rate;
	rate=$(awk '{print $5}' "${log}" | sort | uniq -c | awk '{print $1}' | sort -nr | head -1);

	# if ${rate} is greater than ${limit} then we have failed
	if [ "${rate}" -gt "${limit}" ]; then
		echo "${id}: test run failed, ${rate}/sec exceeded limit of ${limit}/${interval}";
		cat "${log}";
		exit "${EXIT_PUBMED_LIMIT_EXCEEDED}";
	fi

	# shut down the server and remove the logs
	shutdown "${server_pid}" "${rsp}" "${log}";

	return 0;
}


# test_ivratelimiter_crossref <nreq> <njobs> <limit> <interval>
#
# Send <nreq> requests in parallel (up to <njobs>) to ivratelimiter using the
# crossref workflow, we expect no more than the specified <limit> per
# <interval> to arrive from the ivratelimiter to the http server.
#
# The crossref tests dynamically set headers returned by the http server which
# in turn are evaluated by ivratelimiter.
function test_ivratelimiter_crossref () {
	# nreq sets the number of requests to send through ivratelimiter
	local nreq;
	nreq="${1}";
	if [[ ! "${nreq}" =~ ^[1-9][0-9]* ]]; then
		echo "${id}: nreq must be a positive integer" 1>&2;
		exit "${EXIT_BAD_NREQ}";
	fi

	# njobs sets the number of parallel requests to submit to ivratelimiter
	local njobs;
	njobs="${2}";
	if [[ ! "${njobs}" =~ ^[1-9][0-9]* ]]; then
		echo "${id}: njobs must be a positive integer" 1>&2;
		exit "${EXIT_BAD_NJOBS}";
	fi
	
	# limit sets the x-crossref-limit-limit value
	local limit;
	limit="${3}";
	if [[ ! "${limit}" =~ ^[1-9][0-9]* ]]; then
		echo "${id}: limit must be a positive integer" 1>&2;
		exit "${EXIT_BAD_LIMIT}";
	fi

	# interval sets the x-crossref-limit-interval value
	local interval;
	interval="${4}";
	if [[ ! "${interval}" =~ ^[1-9][0-9]* ]]; then
		echo "${id}: interval must be a positive integer" 1>&2;
		exit "${EXIT_BAD_INTERVAL}";
	fi

	# set up a temp file for the response body
	local rsp;
	if ! rsp=$(mktemp); then
		echo "${id}: unable to create temp response file";
		exit "${EXIT_MKTEMP_FAILED}";
	else
		# set up the http response body using the specified limit and
		# interval (Crossref says interval will always be in seconds,
		# e.g., values such as 1s or 10s)
		http_response "${rsp}" "200 OK" "${limit}" "${interval}s";
	fi
	
	# set up a temp file for the server log
	local log;
	if ! log=$(mktemp); then
		echo "${id}: unable to create temp access log";
		exit "${EXIT_MKTEMP_FAILED}";
	fi
	
	# launch the fake http server
	local server_pid;
	server_pid=$(launch_server "${log}" -a "${backend_addr}" -f "${rsp}");
	if [ "${server_pid}" = "" ]; then
		echo "${id}: unable to launch fake http server";
		exit "${EXIT_SERVER_FAILED}";
	fi

	# on exit shut down the fake http server and remove the logs
	trap 'shutdown "${server_pid}" "${rsp}" "${log}"' INT EXIT;
	
	# send the requests as limited by nreq and njobs.
	send_requests "crossref" "${nreq}" "${njobs}";

	# expected_rate is the requests per second limit we expect to see
	local expected_rate;
	expected_rate=$(echo "${limit} / ${interval}" | bc -l | cut -d. -f1);

	# compute the maximum requests per second rate that hit the fake server
	# after passing through ivratelimiter
	local rate;
	rate=$(awk '{print $5}' "${log}" | sort | uniq -c | awk '{print $1}' | sort -nr | head -1);

	# if ${rate} is greater than ${limit}/${interval} then we have failed.
	if [ "${rate}" -gt "${expected_rate}" ]; then
		echo "${id}: test run failed, ${rate}/${interval}s exceeded limit of ${limit}/${interval}s";
		cat "${log}";
		exit "${EXIT_CROSSREF_LIMIT_EXCEEDED}";
	fi

	# shut down the ivratelimiter_httpd and remove the log
	shutdown "${server_pid}" "${rsp}" "${log}";

	return 0;
}

function test_retry_after () {
	local backend;
	backend="${1}";

	local status;
	status="${2}";

	# compute a retry-after a few seconds into the future
	local future;
	future=10

	local retry_after;
	retry_after=$(date -u -d "${future} seconds" +'%a, %d %b %Y %H:%M:%S GMT');

	local expect_date;
	expect_date=$(date -d "${retry_after}" +'%d/%b/%Y:%H:%M:%S');

	# rc will hold the return code from the awk script
	local rc;

	# set up a temp file for the response body
	local rsp;
	if ! rsp=$(mktemp); then
		echo "${id}: unable to create temp response file";
		exit "${EXIT_MKTEMP_FAILED}";
	else
		# set up the http response body with Retry-After
		http_response "${rsp}" "${status}" "" "" "${retry_after}";
	fi
	
	# set up a temp file for the server log
	local log;
	if ! log=$(mktemp); then
		echo "${id}: unable to create temp access log";
		exit "${EXIT_MKTEMP_FAILED}";
	fi
	
	# launch the fake http server
	local server_pid;
	server_pid=$(launch_server "${log}" -a "${backend_addr}" -f "${rsp}");
	if [ "${server_pid}" = "" ]; then
		echo "${id}: unable to launch fake http server";
		exit "${EXIT_SERVER_FAILED}";
	fi

	# on exit shut down the fake http server and remove the logs
	trap 'shutdown "${server_pid}" "${rsp}" "${log}"' INT EXIT;
	
	# send one request, which we expect will result in a 429 or 503
	send_requests "${backend}" "1" "1";

	# reset http_response to a success
	http_response "${rsp}";

	# send a request with a different backend, which we expect to be
	# processed immediately
	case "${backend}" in
	crossref)
		send_requests "pubmed" "1" "1";
		;;
	pubmed)
		send_requests "crossref" "1" "1";
		;;
	*)
		echo "unhandled backend: ${backend}" 1>&2;
		exit "${EXIT_UNKNOWN_ID}";
		;;
	esac

	# send a request, which we expect will wait until the expect_date
	# before hitting the server
	send_requests "${backend}" "1" "1";

	# send a request, which we expect will not wait
	send_requests "${backend}" "1" "1";

	# we expect:
	#  - 4 log entries
	#  - the first log entry to have returned ${status}
	#  - the second log entry to have returned 200 and to be before expect_date
	#  - the 3rd and 4th log entry to have returned 200 and to be on or after expect_date
	#  - the 4th log entry to be within a second of the 3rd 
	awk -v status="${status}" -v expect_date="${expect_date}" '
	BEGIN {
		aborted = 0;
		expect_unix_time = unix_dt(expect_date);
	}
	NR == 1 {
		if ($10 != status) {
			printf("error: expected record %d to return status %s, got %s\n", NR, status, $10);
			aborted = 1;
			exit 1;
		}
	}
	NR == 2 {
		if ($10 != "200") {
			printf("error: expected record %d to return status %s, got %s\n", NR, "200", $10);
			aborted = 1;
			exit 1;
		}
		if (unix_dt($5) >= expect_unix_time) {
			printf("error: expected 2nd request to arrive before %s, got %s:\n\t%s",
				expect_date, substr($5, 2), $0);
			aborted = 1;
			exit 1;
		}
	}
	NR == 3 {
		if ($10 != "200") {
			printf("error: expected record %d to return status %s, got %s\n", NR, "200", $10);
			aborted = 1;
			exit 1;
		}
		blocked_request_time = unix_dt($5);
		if (expect_unix_time > blocked_request_time) {
			printf("error: expected 3rd request to arrive after %s, got %s:\n\t%s\n",
				expect_date, substr($5, 2), $0);
			aborted = 1;
			exit 1;
		}
	}
	NR == 4 {
		if ($10 != "200") {
			printf("error: expected record %d to return status %s, got %s\n", NR, "200", $10);
			aborted = 1;
			exit 1;
		}
		delta = (unix_dt($5) - blocked_request_time)
		if (delta > 2) {
			printf("error: expected 4th r4equest to arrive within 2 seconds of 3rd, got %d seconds\n",
				delta);
		}
	}
	END {
		if (aborted == 0 && NR != 4) {
			printf("error: expected 4 log entries, got %d:\n\t%s\n", NR, $0);
			exit 1;
		}
	}
	func unix_dt(s,  arr) {
		sub(/^\[/, "", s);

		sub(/Jan/, "01", s);
		sub(/Feb/, "02", s);
		sub(/Mar/, "03", s);
		sub(/Apr/, "04", s);
		sub(/May/, "05", s);
		sub(/Jun/, "06", s);
		sub(/Jul/, "07", s);
		sub(/Aug/, "08", s);
		sub(/Sep/, "09", s);
		sub(/Oct/, "10", s);
		sub(/Nov/, "11", s);
		sub(/Dec/, "12", s);

		gsub(/[:/]/, " ", s)

		split(s, arr, " ")

		s = sprintf("%s %s %s %s %s %s",
			arr[3], arr[2], arr[1], arr[4], arr[5], arr[6]);

		return mktime(s, 1)
	}' "${log}"

	rc=$?;

	shutdown "${server_pid}" "${rsp}" "${log}";

	if [ "${rc}" != 0 ]; then
		exit "${EXIT_RETRY_AFTER_ERR}";
	fi
}

# test crossref using a mix of x-crossref-limit-limit and
# x-crossref-limit-interval values
if test_ivratelimiter_crossref 250 20 50 1; then
	echo "${id}: crossref 50/1s rate limit test succeeded";
fi

if test_ivratelimiter_crossref 250 20 25 1; then
	echo "${id}: crossref 25/1s rate limit test succeeded";
fi

if test_ivratelimiter_crossref 250 20 15 1; then
	echo "${id}: crossref 15/1s rate limit test succeeded";
fi

if test_ivratelimiter_crossref 250 20 50 2; then
	echo "${id}: crossref 50/2s rate limit test succeeded";
fi

# the pubmed rate limit is hard-coded inside ivratelimiter to 9/1s
if test_ivratelimiter_pubmed 45 20 9; then
	echo "${id}: pubmed 9/1s rate limit test succeeded";
fi

# test retry-after handling
for backend in "crossref" "pubmed"; do
	if test_retry_after "${backend}" "429"; then
		echo "${id}: crossref w/ Retry-After test succeeded";
	fi
done
