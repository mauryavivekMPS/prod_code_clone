# !/usr/bin/env python
import sys
import os
import time
import csv
import re
from getopt import getopt
import traceback

os.sys.path.append(os.environ['IVETL_ROOT'])

from ivetl.common import common
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.connectors import DoiProxyConnector, SassConnector
from ivetl.models import DoiTransformRule, PublishedArticle, PublishedArticleValues, PublisherJournal

opts, args = getopt(sys.argv[1:], 'hp:j:o:e:t', [
    'help',
    'publisher',
    'journal',
    'outfile',
    'exportfile,'
    'toc'])

publisher_id = None
journal = None
exportfile = 'published_article_type_clean_export.tsv'
updatefile = 'published_article_type_updates.tsv'
difffile = 'published_article_type_diff.tsv'
pavfile = 'published_article_value_article_type_delete.tsv'

test = False

helptext = '''usage: python reset_published_article_type.py -- [ -h ] -p publisher_id -j article_journal
Query the published_article_values table in Cassandra, export values for analysis,
and optionally reset article_type values to HighWire atom store values.
Useful for undoing problematic article_types introduced by a publisher FOAM file.

Environment variables:
This script uses the open_cassandra_connection and close_cassandra_connection
routines defined in celery.py, which in turn use variables defined in common.py.
The Cassandra IP list can be set with the following variable, e.g:
export IVETL_CASSANDRA_IP=bk-vizor-dev-01.highwire.org
Use a comma separated list for multiple hosts.
Options and arguments:
-h     :  print this help message and exit (also --help)
-o     :  output file path to write to. Default: /iv/working/misc/{publisher-id}-rejected_article_export.tsv
-p     :  publisher_id value to use when querying cassandra. required.
-j     :  article_journal value to use when querying cassandra.
-t     :  write updates to cassandra.
'''

basedir = '/iv/working/misc/'
toc = False

for opt in opts:
    if opt[0] == '-h':
        print(helptext)
        sys.exit()
    if opt[0] == '-t':
        toc = True
        print('initializing TOC overwrite')
    if opt[0] == '-p':
        publisher_id = opt[1]
        print('initializing single publisher run: %s' % publisher_id)
    if opt[0] == '-j':
        journal = opt[1]
        print('initializing single journal run: %s' % journal)
    if opt[0] == '-o':
        exportfile = opt[1]
        basedir = ''
        print('initializing output file: %s' % exportfile)

if basedir == '/iv/working/misc/':
    exportfile = '{}-{}'.format(publisher_id, exportfile)
    updatefile = '{}-{}'.format(publisher_id, updatefile)
    difffile = '{}-{}'.format(publisher_id, difffile)
    pavfile = '{}-{}'.format(publisher_id, pavfile)

filepath = basedir + exportfile
update_filepath = basedir + updatefile
diff_filepath = basedir + difffile
pav_filepath = basedir + pavfile

model = ['publisher_id', 'article_doi', 'article_journal', 'article_type', 'subject_category', 'article_title']
pav_model = ['publisher_id', 'article_doi', 'source', 'name', 'value_text']

issn_to_hw_journal_code = {}
transform_rules_by_journal_code = {}

doi_proxy = DoiProxyConnector()
sass = SassConnector()
product_id = 'published_articles'

open_cassandra_connection()

issn_to_hw_journal_code = {j.electronic_issn: j.journal_code for j in PublisherJournal.objects.filter(publisher_id=publisher_id, product_id=product_id)}
issn_to_hw_journal_code.update({j.print_issn: j.journal_code for j in PublisherJournal.objects.filter(publisher_id=publisher_id, product_id=product_id)})

# private function adapted from ivetl/pipelines/publishedarticles/tasks/get_highwire_metadata
def generate_match_pattern(example_doi):
    pattern = ''
    num_non_alphas = 0

    def _non_alpha_re(n):
        return '[^a-z]' + ('{%s}' % n if n > 1 else '')

    for c in example_doi:
        if c.isalpha():
            if num_non_alphas:
                pattern += _non_alpha_re(num_non_alphas)
                num_non_alphas = 0
            pattern += c
        else:
            num_non_alphas += 1

    if num_non_alphas:
        pattern += _non_alpha_re(num_non_alphas)

    return '^' + pattern + '$'

# private function adapted from ivetl/pipelines/publishedarticles/tasks/get_highwire_metadata
def generate_transform_spec(hw_doi):
    spec = ''
    for c in hw_doi:
        if c.isalpha():
            spec += 'L' if c.islower() else 'U'
        else:
            spec += '.'
    return spec

# private function adapted from ivetl/pipelines/publishedarticles/tasks/get_highwire_metadata
def transform_doi(doi, spec):
    transformed_doi = ''
    for i in range(len(spec)):
        if spec[i] == 'L':
            transformed_doi += doi[i].lower()
        elif spec[i] == 'U':
            transformed_doi += doi[i].upper()
        else:
            transformed_doi += doi[i]
    return transformed_doi

# private function adapted from ivetl/pipelines/publishedarticles/tasks/get_highwire_metadata
def get_example_doi_for_issn(issn):
    crossref = CrossrefConnector()
    return crossref.get_example_doi_for_journal(issn)

# private function adapted from ivetl/pipelines/publishedarticles/tasks/get_highwire_metadata
def generate_doi_transform_rule(doi):
    doi_proxy = DoiProxyConnector()
    hw_doi = doi_proxy.get_hw_doi(doi)
    match_expression = generate_match_pattern(doi)
    transform_spec = generate_transform_spec(hw_doi)
    return match_expression, transform_spec

# private function adapted from ivetl/pipelines/publishedarticles/tasks/get_highwire_metadata
def get_article_metadata(article):
    '''Adaptation of code from ivetl/pipelines/publishedarticles/tasks/get_highwire_metadata.py
    which is unfortunately tightly coupled to itself.
    The function isolates some of the pipeline cdoe so it can be run manually
    to patch up data in the database.
    '''
    data = article
    doi = common.normalizedDoi(article.article_doi)
    issn = article.article_journal_issn
    hw_journal_code = None
    if issn and (len(issn) > 0) and issn in issn_to_hw_journal_code:
        hw_journal_code = issn_to_hw_journal_code[issn]

    if not hw_journal_code:
        print("No HW journal code for ISSN for %s, skipping" % doi)

    else:
        # check that we have the rules loaded
        if hw_journal_code not in transform_rules_by_journal_code:
            rules = DoiTransformRule.objects.filter(journal_code=hw_journal_code, type='hw-doi')
            transform_rules_by_journal_code[hw_journal_code] = list(rules)

        # find the matching rule
        transform_spec = None
        for rule in transform_rules_by_journal_code[hw_journal_code]:
            if re.match(rule.match_expression, doi):
                transform_spec = rule.transform_spec

        if not transform_spec:
            hw_doi = doi_proxy.get_hw_doi(doi)

            if len(doi) != len(hw_doi):
                print('Found DOI length mismatch, will not create transform spec: %s and %s' % (doi, hw_doi))
            else:
                match_expression = generate_match_pattern(doi)
                transform_spec = generate_transform_spec(hw_doi)

                # save it to the db
                #new_rule = DoiTransformRule.objects.create(
                #    journal_code=hw_journal_code,
                #    type='hw-doi',
                #    match_expression=match_expression,
                #    transform_spec=transform_spec,
                #)

                # whack it in the local cache
                transform_rules_by_journal_code[hw_journal_code].append(new_rule)

        if not transform_spec:
            print('Could not find or create a transform spec for %s, skipping' % doi)
        else:
            if len(transform_spec) != len(doi):
                print('Found DOI length mismatch with spec, skipping: %s and %s' % (doi, transform_spec))
            else:
                # we are not normalizing these because we're specifically
                # trying to perform case sensitive searches
                hw_doi = transform_doi(doi, transform_spec)

                # try transformed
                metadata = sass.get_metadata(publisher_id, hw_journal_code, hw_doi)

                # fallback to uppercase
                if not metadata:
                    metadata = sass.get_metadata(publisher_id, hw_journal_code, doi.upper())

                # fallback to as-is
                if not metadata:
                    metadata = sass.get_metadata(publisher_id, hw_journal_code, doi)

    return metadata

ctr = 0
modified = 0
articles = PublishedArticle.objects.filter(publisher_id=publisher_id).limit(10000000)
with open(filepath, 'w',
    encoding='utf-8') as file, open(update_filepath, 'w',
    encoding='utf-8') as ufile, open(diff_filepath, 'w',
    encoding='utf-8') as dfile, open(pav_filepath, 'w',
    encoding='utf-8') as vfile:
    writer = csv.writer(file, delimiter='\t')
    uwriter = csv.writer(ufile, delimiter='\t')
    dwriter = csv.writer(dfile, delimiter='\t')
    vwriter = csv.writer(vfile, delimiter='\t')
    writer.writerow(model)
    uwriter.writerow(model)
    dwriter.writerow(['state'] + model)
    vwriter.writerow(pav_model)
    for article in articles:
        if article.is_cohort:
            continue
        row = []
        for col in model:
            row.append(article[col])
        writer.writerow(row)
        if not article.article_journal == journal:
            continue
        if not toc:
            continue
        ctr += 1
        metadata = get_article_metadata(article)
        article_type = 'None'
        if 'article_type' in metadata and (metadata['article_type'] != ''):
            article_type = metadata['article_type']
        write_diff = False
        if article.article_type != article_type:
            write_diff = True
            modified += 1
            article.article_type = article_type
            article.save()
            # delete any custom article data / foam overrides
            doi = common.normalizedDoi(article.article_doi)
            try:
                pa_value = PublishedArticleValues.objects.get(article_doi=doi,
                    publisher_id=publisher_id, source='custom',
                    name='article_type')
                pa_value_row = []
                for col in pav_model:
                    pa_value_row.append(pa_value[col])
                vwriter.writerow(pa_value_row)
                pa_value.delete()
            except:
                print('Failed to get PublishedArticleValue: ', doi)
        print(article_type)
        urow = []
        for col in model:
            urow.append(article[col])
        uwriter.writerow(urow)
        if write_diff:
            dwriter.writerow(['Current'] + row)
            dwriter.writerow(['Reset'] + urow)
    print("Updated %s articles" % (ctr,))
    print("Modified %s articles" % (modified,))

close_cassandra_connection()
