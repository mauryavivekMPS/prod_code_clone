#!/usr/bin/awk -f
#
# log.extract.awk - extract url queued time, requested time, and completed time
# from the mipactvizor debug logs
#
# This script processes the DEBUG mode log produced by the impactvizor service
# and produces a report showing the queue time, the request time, and the
# response times for urls
#
# example lines of interest:
#
# [05/Dec/2020 04:25:26.121] INFO [ivratelimiter.api:284] Queued crossref: https://api.crossref.org/works?mailto=vizor-developers@highwirepress.com&rows=30&filter=from-pub-date:2019-04-04,type:journal-article&query=PerampanelInduced Hair Curling in a Patient with Epilepsy Associated with Pitt Hopkins Syndrome
# 
# [05/Dec/2020 04:25:26.122] INFO [ivratelimiter.api:242] Requested crossref: https://api.crossref.org/works?mailto=vizor-developers@highwirepress.com&rows=30&filter=from-pub-date:2019-04-04,type:journal-article&query=PerampanelInduced Hair Curling in a Patient with Epilepsy Associated with Pitt Hopkins Syndrome
# 
# [05/Dec/2020 04:25:31.136] DEBUG [requests.packages.urllib3.connectionpool:401] "GET /works?mailto=vizor-developers@highwirepress.com&rows=30&filter=from-pub-date:2019-04-04,type:journal-article&query=PerampanelInduced%20Hair%20Curling%20in%20a%20Patient%20with%20Epilepsy%20Associated%20with%20Pitt%20Hopkins%20Syndrome HTTP/1.1" 200 169738
# 
# produces an output line:
#
# 1607142326.121 1607142326.122 1607142331.136 https://api.crossref.org/works?mailto=vizor-developers@highwirepress.com&rows=30&filter=from-pub-date:2019-04-04,type:journal-article&query=PerampanelInduced Hair Curling in a Patient with Epilepsy Associated with Pitt Hopkins Syndrome
#

BEGIN {
	month["Jan"] = "01";
	month["Feb"] = "02";
	month["Mar"] = "03";
	month["Apr"] = "04";
	month["May"] = "05";
	month["Jun"] = "06";
	month["Jul"] = "07";
	month["Aug"] = "08";
	month["Sep"] = "09";
	month["Oct"] = "10";
	month["Nov"] = "11";
	month["Dec"] = "12";
}

# capture queued time and scheme+host for this path
/\] Queued [^:]+:/ {
	k = $0;
	sub(/^.*\] Queued [^:]+: https?:\/\/[^\/]+/, "", k);
	k = decode(k);
	queued[k] = unix_dt($1, $2);

	h = $0;
	sub(/^.*\] Queued [^:]+: /, "", h);
	host[k] = substr(h, 1, length(h) - length(k));
}

# capture requested time for this path
/\] Requested [^:]+:/ {
	k = $0;
	sub(/^.*\] Requested [^:]+: https?:\/\/[^\/]+/, "", k); 
	k = decode(k);

	requested[k] = unix_dt($1, $2);
}

# if this url path is in our host, queued, and requested arrays, print out the
# full url, the queued time, the requested time, and the completed time
/HTTP\/1.[01]" [0-9]+ / {
	k = decode($6);

	if (k in host && 
	    k in queued && 
	    k in requested) {
		completed = unix_dt($1, $2);
		print queued[k], requested[k], completed, host[k] k;
	}

	delete host[k];
	delete queued[k]
	delete requested[k];
}

# decode replaces %HH hex encoded strings with ascii
function decode(s, x,n,i,c, dec) {
	n = split(s, x, "%");
	for (i = 1; i <= n; i++) {
		if (x[i] ~ /^[0-9a-fA-F][0-9a-fA-F]/) {
			c = sprintf("%c", strtonum("0x" substr(x[i], 1, 2)));
			dec = dec c substr(x[i], 3);
		} else {
			if ( i == 1 ) {
				dec = x[i];
			} else {
				dec = dec "%" x[i];
			}
		}
	}
	return dec;
}

# convert log date and time components "05/Dec/2020" and "04:25:26.121"
# (assumed to be in UTC) into Unix time seconds with fractional milliseconds,
# 1607142326.121
function unix_dt(s1,s2,  t,k,s) {
	sub(/^\[/, "", s1);
	sub(/]$/, "", s2);
	gsub(/[\/]/, " ", s1);
	gsub(/[:\.]/, " ", s2);

	split(s1 " " s2, t, " ");

	# replace t[2] month name with month number
	for (k in month) {
		if (k == t[2]) {
			t[2] = month[k];
			break;
		}
	}

	# construct s using the format expected by mktime:
	# <year> <month> <day> <hour> <minute> <second>
	s = sprintf("%s %s %s %s %s %s", t[3], t[2], t[1], t[4], t[5], t[6]);

	# assume s to be in utc and conver it to Unix time seconds with
	# fractional milliseconds appended
	return mktime(s, 1) "." t[7]
}
