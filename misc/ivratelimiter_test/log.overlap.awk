#!/usr/bin/awk -f
#
# log.overlap.awk - process output of log.extract.awk to produce a report on
# in-flight requests per second
#

/[0-9]+.[0-9]+ [0-9]+.[0-9]+ [0-9]+.[0-9]+ .+/ {
	q = $1;
	r = $2;
	c = $3;
	u = substr($0, length(q) + length(r) + length(c) + 4);

	for (i = int(r); i <= int(c); i++) {
		inflight[i]++;
	}
}
END {
	for (i in inflight) {
		print strftime("%Y-%m-%d %H:%M:%S", i), inflight[i] | "sort -n";
	}
}
