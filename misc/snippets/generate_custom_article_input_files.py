import sys
import os
import time
import csv
import re
from getopt import getopt
import traceback
from datetime import datetime

os.sys.path.append(os.environ['IVETL_ROOT'])

opts, args = getopt(sys.argv[1:], 'ha:i:j:l:o:v:', [
    'abbr',
    'help',
    'input',
    'journal',
    'values-input',
    'outfile'
    ])


helptext = '''usage: python export_published_articles.py -- [ -h | -i published_articles_input_file | -l published_article_values_input_file ]

Generate custom article input files (aka files of additional metadata / foam)

Environment variables:


Options and arguments:
-a     :  publisher/journal abbreviation for file label
-h     :  print this help message and exit (also --help)
-i     :  input published articles file.
-j     :  journal
-l     :  published article values input file.
-o     :  output file path to write to. Default: /iv/working/misc/vizor_pat_details_{abbr}_database_generated_{YYYY_MM_DD}.tsv
-u     :  determine unique values for various fields and write to a separate file for analysis.
'''



basedir = '/iv/working/misc/'
pa_inputfile = '/iv/working/misc/wkh-published_article_export.tsv'
pav_inputfile = '/iv/working/misc/wkh-published_article_values_export.tsv'
exportfile = ''
journals = []
jset = set()
unique = False
index = {}
abbr = 'jnl'
today = datetime.now().strftime('%Y_%m_%d')

print('opts')
print(opts)

for opt, val in opts:
    if opt in ('-h', '--help'):
        print(helptext)
        sys.exit()
    elif opt in ('-a', '--abbr'):
        abbr = val
    elif opt in ('-i', '--input'):
        pa_inputfile = val
    elif opt in ('-l', '--values-input'):
        pav_inputfile = val
    elif opt in ('-o', '--output-file'):
        exportfile = val
        basedir = ''
        print('initializing output file: %s' % exportfile)
    elif opt in ('-j', '--journal'):
        journals.append(val.lower())
    elif opt in ('-u', '--unique'):
        unique = True

if basedir == '/iv/working/misc/':
    exportfile = 'vizor_pat_details_{}_database_generated_{}.tsv'.format(abbr, today)

filepath = basedir + exportfile

# foam file model
model = ['article_type', 'subject_category', 'editor', 'custom', 'custom_2',
    'custom_3', 'citeable_article', 'is_open_access']

print('journals:')
print(journals)

count = 0

with open(pa_inputfile, 'r') as pafile, open(pav_inputfile,
    'r') as pvfile, open(filepath,
    'w', encoding='utf-8') as outfile:

    pvreader = csv.DictReader(pvfile, delimiter='\t', fieldnames=[
        'publisher_id', 'article_doi', 'source', 'name', 'value_text'
    ])
    next(pvreader, None)

    for value in pvreader:
        if value['source'] != 'custom':
            continue
        doi = value['article_doi']
        if not doi in index:
            index[doi] = {}
        index[doi][value['name']] = value['value_text']

    pvfile.close()

    pareader = csv.DictReader(pafile, delimiter='\t')
    next(pareader, None)

    writer = csv.writer(outfile, delimiter='\t')
    writer.writerow([
        'DOI',
        'TOC_SECTION',
        'COLLECTION',
        'EDITOR',
        'CUSTOM',
        'CUSTOM_2',
        'CUSTOM_3',
        'CITEABLE_ARTICLE',
        'IS_OPEN_ACCESS'
    ])
    for article in pareader:
        row = []
        doi = article['article_doi']
        j = article['article_journal'] if article['article_journal'] else ''
        j = j.lower()
        i = article['article_journal_issn'] if article['article_journal_issn'] else ''
        i = i.lower()
        if count < 20:
            count += 1
            print(j)
            print(i)
            print(doi)
            print(doi in index)
            print((j in journals or i in journals) and doi in index)
        if (j in journals or i in journals) and doi in index:
            row.append(doi)
            for col in model:
                row.append(index[doi][col] if col in index[doi] else '')
            writer.writerow(row)
