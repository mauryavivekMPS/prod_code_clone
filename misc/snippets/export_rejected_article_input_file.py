import sys
import os
import time
import csv
import re
from getopt import getopt
from datetime import datetime
import traceback

os.sys.path.append(os.environ['IVETL_ROOT'])

from ivetl.models import RejectedArticles
from ivetl.celery import open_cassandra_connection, close_cassandra_connection

opts, args = getopt(sys.argv[1:], 'hfj:l:p:o:e:u', [
    'help',
    'full',
    'journal',
    'limit',
    'publisher',
    'outfile',
    'exportfile',
    'unique'])

pubid = None
export_pubid = None
full_export = False
limit = None
exportfile = 'rejected_article_export.tsv'
today = datetime.now().strftime('%Y-%m-%d') 
write_sets = False

helptext = '''usage: python export_rejected_article_input_file.py -- [ -h | -f | -j | -l limit ] -p publisher_id

Generate a rejected article input file for a publisher/journal based on data in Cassandra.

Environment variables:

This script uses the open_cassandra_connection and close_cassandra_connection
routines defined in celery.py, which in turn use variables defined in common.py.
The Cassandra IP list can be set with the following variable, e.g:

export IVETL_CASSANDRA_IP=bk-vizor-dev-01.highwire.org

Use a comma separated list for multiple hosts.

Options and arguments:
-e     :  export publisher id, used in output filename. useful when transferring data from one publisher code to another, e.g. generating a "demo-xx" account or for the wkh migration. If not provided, -p publisher id will be used instead.
-f     :  full export. writes all rows
-h     :  print this help message and exit (also --help)
-j     :  journal title or abbreviation. can be provided multiple times.
-l     :  limit value to use when querying cassandra. default: None (all records)
-o     :  output file path to write to. Default: /iv/working/misc/vizor_rat_{publisher-id}_db_export_{todays date YYYY-MM-DD}.tsv
-p     :  publisher_id value to use when querying cassandra. required.
-u     :  determine unique values for various fields and write to a separate file for analysis.
'''


basedir = '/iv/working/misc/'
journals = []

for opt, val in opts:
    if opt in ('-h', '--help'):
        print(helptext)
        sys.exit()
    elif opt in  ('-f', '--full'):
        full_export = True
    elif opt == ('-l', '--limit'):
        l = val
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
    elif opt in ('-p', '--publisher'):
        pubid = val
        print('initializing single publisher run: %s' % pubid)
    elif opt in ('-e', '--export-publisher'):
        export_pubid = val
        print('using separate id for export file naming: %s' % export_pubid)
    elif opt in ('-o', '--output-file'):
        exportfile = val
        basedir = ''
        print('initializing output file: %s' % exportfile)
    elif opt in ('-j', '--journal'):
        journals.append(val)
    elif opt in ('-u', '--unique'):
        write_sets = True

filename_pubid = export_pubid if export_pubid else pubid

if basedir == '/iv/working/misc/':
    exportfile = 'vizor_rat_%s_db_export_%s' % (filename_pubid, today)

filepath = basedir + exportfile
setfilepath = basedir + 'uniques_' + exportfile

filemodel = ['MANUSCRIPT_ID', 'DATE_OF_REJECTION', 'REJECT_REASON', 'TITLE',
    'FIRST_AUTHOR', 'CORRESPONDING_AUTHOR', 'CO_AUTHORS', 'SUBJECT_CATEGORY',
    'EDITOR', 'SUBMITTED_JOURNAL', 'ARTICLE_TYPE', 'KEYWORDS', 'CUSTOM',
    'FUNDERS', 'CUSTOM_2', 'CUSTOM_3']

ramodel = ['manuscript_id', 'date_of_rejection', 'reject_reason',
    'manuscript_title', 'first_author', 'corresponding_author', 'co_authors',
    'subject_category', 'editor', 'submitted_journal', 'article_type',
    'keywords', 'custom', 'funders', 'custom_2', 'custom_3']

jset = set()
aset = set()
sset = set()
cset = set()

open_cassandra_connection()

rarticles = RejectedArticles.objects.filter(publisher_id=pubid).limit(limit)

with open(filepath, 'w', encoding='utf-8') as file:
    writer = csv.writer(file, delimiter='\t')
    writer.writerow(filemodel)
    for rarticle in rarticles:
        row = []
        jset.add(rarticle.submitted_journal)
        aset.add(rarticle.article_type)
        sset.add(rarticle.subject_category)
        cset.add(rarticle.custom)
        if len(journals) > 0 and rarticle['submitted_journal'] not in journals:
            continue
        for col in ramodel:
            try:
                if 'date' in col:
                    row.append(rarticle[col].strftime('%m/%d/%y'))
                else:
                    row.append(rarticle[col])
            except KeyError:
                # at this time of this writing (2020-04-02),
                # it appears that the 'funders' field,
                # while present in the input file spec and parts of the codebase,
                # was never implemeneted in the database.
                # for some reason, a try / catch block was added to handle this problem:
                # https://github.com/highwire/impactvizor-pipeline/blob/6fec18190b26048de7038f2c264a7cad9e3f73dd/ivetl/pipelines/rejectedarticles/tasks/prepare_input_file.py#L45-L62
                # try:
                #    input_data[field] = r[field]
                # except KeyError:
                #    tlogger.info('Field "' + field + '" is not a database column')
                # instead of just ensuring that the input_data dictionary
                # only contained properties matching database fields?
                row.append('')
        writer.writerow(row)

close_cassandra_connection()

if (write_sets):
    with open(setfilepath, 'w', encoding='utf-8') as sfile:
        writer = csv.writer(sfile, delimiter='\t')
        jrow = ['submitted_journal']
        jrow.extend(jset)
        writer.writerow(jrow)
        arow = ['article_type']
        arow.extend(aset)
        writer.writerow(arow)
        srow = ['subject_category']
        srow.extend(sset)
        writer.writerow(srow)
        crow = ['custom']
        crow.extend(cset)
        writer.writerow(crow)
    sfile.close()
