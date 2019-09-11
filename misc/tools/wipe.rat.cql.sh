#!/bin/bash
#
# wipe.rat.cql.sh - generate CQL commands to wipe RAT data for a publisher
#

# terminate on any error
set -euo pipefail;

# user prints out the script usage and optionally
# exists if arg $1 is passed in
function usage {
	echo "usage: wipe.rat.cql.sh { -all | -subset <manuscript_id.txt> } <publisher_id>";
	if [ "$1" != "" ]; then
		exit "$1";
	fi
}

all_ids="0";
subset="";
publisher_id="";

while [ "${#}" -gt 0 ]; do
	case "${1}" in
	-all|--all)
		all_ids="1";
		;;
	-subset|--subset)
		all_ids="0";
		if [ -f "${2}" ]; then
			subset="${2}";
			shift;
		else
			echo "error: missing manuscript id file argument to -subset: '${2}' is not a file" 1>&2;
			usage 1;
		fi
		;;
	*)
		if [ "${publisher_id}" = "" ]; then
			publisher_id="${1}";
		else
			echo "error: only one publisher_id allowed: '${publisher_id}' was already set";
			usage 1;
		fi
		;;
	esac;
	shift;
done

if [ "${all_ids}" == 0 ] && [ ! -f "${subset}" ]; then
	echo "error: if -all was not specified then -subset must specify a file listing ids." 1>&2;
	usage 1;
fi

if [ -f "${subset}" ] && [ ! -s "${subset}" ] ; then
	echo "error: -subset file must not be zero length: ${subset}" 1>&2;
	usage 1;
fi

if [ -z "${publisher_id}" ]; then
	echo "error: missing required publisher_id argument" 1>&2;
	usage 1;
fi

# cqldump pipes a CQL request through cqlsh with paging turned off,
# then reformats the output into a TSV
function cqldump {
	echo "PAGING OFF; $*" | cqlsh --request-timeout=3600 | sed '
		s/ | /	/g;
		s/  */ /g;
		s/ 	/	/g;
		s/	 /	/g;
		s/^ //;
		s/ $//;
		/^[-+][-+]*$/d;
		/^Disabled Query paging.$/d;
		/^([0-9][0-9]* rows)$/d;
		/^$/d;';
}

# step one, dump the impactvizor.rejected_articles table for
# the publisher, possibly filtering by manuscript_id if
# all_ids is zero and subsets has been defined.
original="${publisher_id}.rejected_articles.tsv";
cqldump "SELECT * FROM impactvizor.rejected_articles WHERE publisher_id = '${publisher_id}';" \
	| awk -F"\t" -v all_ids="${all_ids}" -v subset="${subset}" '
		BEGIN{
			nrec = 0;
			if ( all_ids == 0 ) {
				n = 0;
				while((getline < subset) > 0) {
					id = $1;
					gsub(/\r/, "", id);
					manuscript_id[id] = 1;
					n++;
				}
				if (n == 0) {
					printf("error: zero manuscript_id read from file: %s\n", subset) | "cat 1>&2";
				}
			}
		}
		NR == 1 {
			if (all_ids == 0) {
				id = 0;
				for (i = 1; i <= NF; i++) {
					 if ($i == "manuscript_id") {
						id = i;
						break;
					 }
				}
				if (id == 0) {
					printf("error: unable to identify manuscript_id field from line 1 of %s", subset) | "cat 1>&2";
				}
			}
			print $0;
		}
		NR > 1 {
			if (all_ids == 0) {
				if ( $id in manuscript_id ) {
					print $0;
					nrec++;
				}
			} else {
				print $0;
				nrec++;
			}
		}' \
	| gzip -9c > "${original}.gz";

# step two, confirm the publisher_id count in the data
zcat "${original}.gz" | awk -F'\t' '
	NR > 1 {
		if (! ($1 in corpus)) {
			ncorpus++;
		}
		corpus[$1]++;
		t++;
	}
	END{
		if (t == 0) {
			printf("zero rows selected from rejected_articles, nothing to do.\n") > "/dev/stderr";
			exit 1;
		}
		if (ncorpus != 1) {
			printf("expected exactly 1 corpus code, found %d\n", ncorpus) > "/dev/stderr";
			exit 1;
		}
	}'

# step three, build a 'delete' set for rejected_articles
rejected_articles_batch="${publisher_id}.rejected_articles.delete.cql";
zcat "${original}.gz" | awk -F'\t' '
	NR == 1 {
		for (i = 1; i <= NF; i++) {
			if ($i == "publisher_id") {
				publisher_id = i;
			}
			if ($i == "rejected_article_id") {
				rejected_article_id = i;
			}
		}
		if ( publisher_id == 0) {
			printf("error: unable to determine column for publisher_id\n") > "/dev/stderr";
			exit 1;
		}
		if ( rejected_article_id == 0 ) {
			printf("error: unable to determine column for rejected_article_id\n") > "/dev/stderr";
			exit 1;
		}
	}
	NR > 1 {
		printf("DELETE FROM impactvizor.rejected_articles WHERE publisher_id = \047%s\047 AND rejected_article_id = %s;\n", $publisher_id, $rejected_article_id);
	}
' | gzip -9c > "${rejected_articles_batch}.gz";

# step four, build an 'update' set for published_article
published_article_batch="${publisher_id}.published_article.update.cql";
zcat "${original}.gz" | awk -F'\t' -vpublisher_id="${publisher_id}" '
	NR == 1 {
		for (i = 1; i <= NF; i++) {
			if ($i == "crossref_doi") {
				crossref_doi = i;
			}
		}
		if ( crossref_doi == 0 ) {
			printf("error: unable to determine column for crossref_doi\n") > "/dev/stderr";
			exit 1;
		}
	}
	NR > 1 && $crossref_doi != "null" {
		printf("UPDATE impactvizor.published_article SET date_of_rejection = null, from_rejected_manuscript = false, rejected_manuscript_editor = null, rejected_manuscript_id = null WHERE publisher_id = \047%s\047 AND article_doi = \047%s\047;\n", publisher_id, $crossref_doi)}' | gzip -9c > "${published_article_batch}.gz";

printf "%s: generated the following files:\n\n" "$0";

ls -l "${rejected_articles_batch}.gz" "${published_article_batch}.gz" | sed 's,^,	,';

cat <<EOF

please review them, e.g.,

	zcat '${rejected_articles_batch}.gz' | less;
	zcat '${published_article_batch}.gz' | less;

and if satisfied, execute them:

	zcat '${rejected_articles_batch}.gz' | cqlsh;
	zcat '${published_article_batch}.gz' | cqlsh;

To update Tableau, go to

   http://reports.vizors.org/#/projects/

and select your publisher.

Next select the 'Data Sources' tab from the top row.

Select the checkbox next to the row 'rejected_articles_ds_${publisher_id}'.

Select 'Refresh Extracts' from the 'Action' pull-down that should
appear toward the top left, and run a Full Refresh now, or schedule
it for the time you desire.

Navigating over to the 'Status' tab

        http://reports.vizors.org/#/server/status

and selecting 'Background Tasks for Extracts'

    http://reports.vizors.org/#/server/analysis/BackgroundTasksforExtracts

lets you then monitor the status of the job.
EOF
