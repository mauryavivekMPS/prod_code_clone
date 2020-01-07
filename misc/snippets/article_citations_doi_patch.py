import sys
import os
import time
import csv
import re
from getopt import getopt
from datetime import datetime
import traceback

os.sys.path.append(os.environ['IVETL_ROOT'])

start = datetime.now()

from ivetl.models import ArticleCitations
from ivetl.celery import open_cassandra_connection, close_cassandra_connection

opts, args = getopt(sys.argv[1:], 'hfl:p:o:e:', [
    'help',
    'full',
    'limit',
    'publisher',
    'outfile',
    'exportfile'])

pubid = None
full_export = False
limit = None
capfile = 'artcit_export_capitals.tsv'
exportfile = 'artcit_export.tsv'
dupfile = 'artcit_export_duplicates.tsv'
dauditfile = 'artcit_export_keeps.tsv'
delfile = 'artcit_export_deletes.tsv'
del2file = 'artcit_delete_input.tsv'
merfile = 'artcit_merge_input.tsv'
mauditfile = 'artcit_merge_audit.tsv'

helptext = '''usage: python doi_export.py [ -h | -f | -l limit ] -p publisher_id

Query the article_citations table in Cassandra and look for duplicates.

Environment variables:

This script uses the open_cassandra_connection and close_cassandra_connection
routines defined in celery.py, which in turn use variables defined in common.py.
The Cassandra IP list can be set with the following variable, e.g:

export IVETL_CASSANDRA_IP=bk-vizor-dev-01.highwire.org

Use a comma separated list for multiple hosts.

Options and arguments:
-f     :  full export. writes an additional file with all rows, not just duplicates
-h     :  print this help message and exit (also --help)
-l     :  limit value to use when querying cassandra. default: None (all records)
-p     :  publisher_id value to use when querying cassandra. required.
'''


for opt in opts:
    if opt[0] == '-h':
        print(helptext)
        sys.exit()
    if opt[0] == '-f':
        full_export = True
    if opt[0] == '-l':
        l = opt[1]
        if l == 'None' or l == 'none':
            limit = None
        elif type(l) is str:
            try:
                limit = int(l)
            except:
                print('Failed to parse limit value to int: %s' % l)
                sys.exit()
        else:
            limit = l
    if opt[0] == '-p':
        pubid = opt[1]
        print('initializing single publisher run: %s' % pubid)
    if opt[0] == '-o':
        capfile = opt[1]
        print('initializing output filename: %s' % capfile)

basedir = '/iv/working/misc/'

capfile_path = os.path.join(basedir, '%s_%s' % (pubid, capfile))
exportfile_path = os.path.join(basedir, '%s_%s' % (pubid, exportfile))
dupfile_path = os.path.join(basedir, '%s_%s' % (pubid, dupfile))
dauditfile_path = os.path.join(basedir, '%s_%s' % (pubid, dauditfile))
delfile_path = os.path.join(basedir, '%s_%s' % (pubid, delfile))
del2file_path = os.path.join(basedir, '%s_%s' % (pubid, del2file))
merfile_path = os.path.join(basedir, '%s_%s' % (pubid, merfile))
mauditfile_path = os.path.join(basedir, '%s_%s' % (pubid, mauditfile))
statfile_path = os.path.join(basedir, '%s_doi_export_stats.txt' % pubid)
if not pubid:
    print('Please supply a publisher id with the -p flag')
    sys.exit()

nomatch = 0
count = 0
duplicates = 0
uniquedupdois = 0
deletes = 0
keeps = 0

# django models normally provide a _meta.fields() api,
#     however this does not appear to be implemented in the cassandra driver 
#     models we use
# hardcoded article_citation fields for convenience

fields = [
    'publisher_id',
    'article_doi',
    'citation_doi',
    'citation_date',
    'citation_first_author',
    'citation_issue',
    'citation_journal_issn',
    'citation_journal_title',
    'citation_pages',
    'citation_scopus_id',
    'citation_sources',
    'citation_source_scopus',
    'citation_source_xref',
    'citation_title',
    'citation_volume',
    'citation_count',
    'created',
    'updated',
    'is_cohort',
]
header = []
for field in fields:
    header.append(field)

keyidx = {}

with open(capfile_path, 'w',
    encoding='utf-8') as outf, open(exportfile_path, 'w',
    encoding='utf-8') as expf, open(dupfile_path, 'w',
    encoding='utf-8') as dupf, open(dauditfile_path, 'w',
    encoding='utf-8') as audf, open(delfile_path, 'w',
    encoding='utf-8') as delf, open(del2file_path, 'w',
    encoding='utf-8') as del2f, open(merfile_path, 'w',
    encoding='utf-8') as merf, open(mauditfile_path, 'w',
    encoding='utf-8') as maudf, open(statfile_path, 'w',
    encoding='utf-8') as statf:
    outwriter = csv.writer(outf, delimiter='\t')
    expwriter = csv.writer(expf, delimiter='\t')
    dupwriter = csv.writer(dupf, delimiter='\t')
    audwriter = csv.writer(audf, delimiter='\t')
    delwriter = csv.writer(delf, delimiter='\t')
    del2writer = csv.writer(del2f, delimiter='\t')
    merwriter = csv.writer(merf, delimiter='\t')
    maudwriter = csv.writer(maudf, delimiter='\t')
    statwriter = csv.writer(statf, delimiter='\t')

    outwriter.writerow(header)
    expwriter.writerow(header)

    open_cassandra_connection()

    for ac in ArticleCitations.objects.filter(publisher_id=pubid).limit(limit):
        count += 1
        exportrow = []
        for field in fields:
            exportrow.append(getattr(ac, field))
        if full_export:
            expwriter.writerow(exportrow)
        article_doi = ac.article_doi
        lc_article_doi = ac.article_doi.lower()
        citation_doi = ac.citation_doi
        lc_citation_doi = ac.citation_doi.lower()
        key = lc_article_doi + '__' + lc_citation_doi
        if key not in keyidx:
            keyidx[key] = [ exportrow ]
        else:
            keyidx[key].append(exportrow)
        if article_doi != lc_article_doi or citation_doi != lc_citation_doi:
            nomatch += 1
            outwriter.writerow(exportrow)

    close_cassandra_connection()

    dupwriter.writerow(header)
    audwriter.writerow(header)
    delwriter.writerow(header)
    maudwriter.writerow(header)
    for key, keylist in keyidx.items():
        if len(keylist) > 1:
            uniquedupdois += 1
            delrows = []
            keeprow = None
            for row in keylist:
                duplicates += 1
                dupwriter.writerow(row)
                scopusid = row[9]
                if type(scopusid) is str and re.match(r'2-s2\.0-\d+',
                    scopusid) is not None:
                    delrows.append(row)
                    continue
                if keeprow is None:
                    keeprow = row
                    continue
                # prefer rows with citation_date values
                if isinstance(row[3], datetime) and not isinstance(keeprow[3],
                    datetime):
                    delrows.append(keeprow)
                    keeprow = row
                    continue
                elif isinstance(keeprow[3], datetime) and not isinstance(row[3],
                    datetime):
                    delrows.append(row)
                    continue
                elif isinstance(keeprow[3], datetime) and isinstance(row[3],
                    datetime):
                    # check for higher precision date;
                    # assume year-only inserted as YYYY-01-01
                    if keeprow[3].month == 1 and row[3].month > 1:
                        delrows.append(keeprow)
                        keeprow = row
                        continue
                    elif keeprow[3].month > 1 and row[3].month == 1:
                        delrows.append(row)
                        continue
                    elif keeprow[3].month == 1 and row[3].month == 1:
                        if keeprow[3].day == 1 and row[3].day > 1:
                            delrows.append(keeprow)
                            keeprow = row
                            continue
                        elif keeprow[3].day > 1 and row[3].day == 1:
                            delrows.append(row)
                            continue
                # col 11 = citation_source_scopus - True for MAG or Scopus
                # col 12 = citation_source_xref - True for CrossRef
                # scopus-style IDs stripped above,
                # this block prefers XREF source over MAG
                if row[12] and not keeprow[12]:
                    delrows.append(keeprow)
                    keeprow = row
                    continue
                elif keeprow[12] and not row[12]:
                    delrows.append(row)
                    continue
                # col 17 = updated datetime
                # if all else fails, prefer most recent
                keepdate = keeprow[17]
                rowdate = row[17]
                if rowdate > keepdate:
                    delrows.append(keeprow)
                    keeprow = row
                else:
                    delrows.append(row)
            # if all were deleted due to scopus id re match, keep the last one
            if keeprow is None:
                keeprow = delrows.pop()
            for delrow in delrows:
                deletes += 1
                delwriter.writerow(delrow)
                del2writer.writerow([
                    delrow[0],
                    delrow[1],
                    delrow[2]
                ])
            keeps += 1
            audwriter.writerow(keeprow)
            # check for missing data in keeprow, add to merge file
            mergerow = keeprow
            # col 6 = citation_journal_issn
            if not keeprow[6]:
                for delrow in delrows:
                    if delrow[6]:
                        mergerow[6] = delrow[6]
                        break;
            # col 7 = citation_journal_title
            if not keeprow[7]:
                for delrow in delrows:
                    if delrow[7]:
                        mergerow[7] = delrow[7]
                        break;
            maudwriter.writerow(mergerow)
            merwriter.writerow([
                mergerow[0],
                mergerow[1],
                mergerow[2],
                mergerow[6],
                mergerow[7]
            ])


    statwriter.writerow([ 'publisher_id', pubid ])
    statwriter.writerow([ 'rows with capitalization', nomatch ])
    statwriter.writerow([ 'duplicate rows', duplicates ])
    statwriter.writerow(['unique DOIs with 1 or more duplicates', uniquedupdois])
    percent = '{:.1%}'.format((duplicates - uniquedupdois)/count)
    statwriter.writerow(['% duplicates', percent])
    statwriter.writerow([ 'total db rows', count ])
    statwriter.writerow([ 'delete rows written', deletes])
    statwriter.writerow([ 'audit/keep rows written', keeps])
    elapsed = datetime.now() - start
    statwriter.writerow([ 'elapsed time', elapsed ])

    outf.close()
    expf.close()
    statf.close()
    dupf.close()
    audf.close()
    delf.close()
    del2f.close()
    merf.close()
    maudf.close()
