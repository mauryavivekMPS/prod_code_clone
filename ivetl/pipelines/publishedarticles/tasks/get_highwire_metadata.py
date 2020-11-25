import codecs
import csv
import json
import os
import re
import threading

from ivetl.celery import app
from ivetl.common import common
from ivetl.connectors import CrossrefConnector, DoiProxyConnector, SassConnector
from ivetl.models import PublisherJournal, DoiTransformRule
from ivetl.pipelines.task import Task


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


def generate_transform_spec(hw_doi):
    spec = ''
    for c in hw_doi:
        if c.isalpha():
            spec += 'L' if c.islower() else 'U'
        else:
            spec += '.'
    return spec


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


def get_example_doi_for_issn(issn):
    crossref = CrossrefConnector()
    return crossref.get_example_doi_for_journal(issn)


def generate_doi_transform_rule(doi):
    doi_proxy = DoiProxyConnector()
    hw_doi = doi_proxy.get_hw_doi(doi)
    match_expression = generate_match_pattern(doi)
    transform_spec = generate_transform_spec(hw_doi)
    return match_expression, transform_spec


@app.task
class GetHighWireMetadataTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        file = task_args['input_file']

        product = common.PRODUCT_BY_ID[product_id]

        # if cohort product, skip this task
        if product['cohort']:
            tlogger.info("Cohort product - Skipping Task")
            return task_args

        target_file_name = work_folder + "/" + publisher_id + "_" + "hwmetadatalookup" + "_" + "target.tab"

        issn_to_hw_journal_code = {j.electronic_issn: j.journal_code for j in PublisherJournal.objects.filter(publisher_id=publisher_id, product_id=product_id)}
        issn_to_hw_journal_code.update({j.print_issn: j.journal_code for j in PublisherJournal.objects.filter(publisher_id=publisher_id, product_id=product_id)})

        already_processed = set()

        # if the file exists, read it in assuming a job restart
        if os.path.isfile(target_file_name):
            with codecs.open(target_file_name, encoding='utf-16') as tsv:
                for line in csv.reader(self.reader_without_unicode_breaks(tsv), delimiter='\t'):
                    if line and len(line) == 4 and line[0] != 'PUBLISHER_ID':
                        doi = common.normalizedDoi(line[1])
                        already_processed.add(doi)

        if already_processed:
            tlogger.info('Found %s existing items to reuse' % len(already_processed))

        target_file = codecs.open(target_file_name, 'a', 'utf-16')
        if not already_processed:
            target_file.write('\t'.join(['PUBLISHER_ID', 'DOI', 'ISSN', 'DATA']) + '\n')

        article_rows = []

        # read everything in from the input file first
        line_count = 0
        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):

                line_count += 1
                if line_count == 1:
                    continue

                publisher_id = line[0]
                doi = common.normalizedDoi(line[1])
                issn = line[2]
                data = json.loads(line[3])

                if doi in already_processed:
                    continue

                article_rows.append((doi, issn, data))

        count = 0
        count_lock = threading.Lock()

        total_count = len(article_rows)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        tlogger.info('Total articles to be processed: %s' % total_count)

        transform_rules_by_journal_code = {}

        doi_proxy = DoiProxyConnector()
        sass = SassConnector(tlogger=tlogger)

        def process_article_rows(article_rows_for_this_thread):
            nonlocal count

            thread_article_count = 0

            for article_row in article_rows_for_this_thread:
                with count_lock:
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                thread_article_count += 1

                doi, issn, data = article_row

                tlogger.info("Retrieving metadata for: %s" % doi)

                hw_journal_code = None
                if 'ISSN' in data and (len(data['ISSN']) > 0) and data['ISSN'][0] in issn_to_hw_journal_code:
                    hw_journal_code = issn_to_hw_journal_code[data['ISSN'][0]]

                if not hw_journal_code:
                    tlogger.info("No HW journal code for ISSN for %s, skipping" % doi)

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
                            tlogger.info('Found DOI length mismatch, will not create transform spec: %s and %s' % (doi, hw_doi))
                        else:
                            match_expression = generate_match_pattern(doi)
                            transform_spec = generate_transform_spec(hw_doi)

                            # save it to the db
                            new_rule = DoiTransformRule.objects.create(
                                journal_code=hw_journal_code,
                                type='hw-doi',
                                match_expression=match_expression,
                                transform_spec=transform_spec,
                            )

                            # whack it in the local cache
                            transform_rules_by_journal_code[hw_journal_code].append(new_rule)

                    if not transform_spec:
                        tlogger.info('Could not find or create a transform spec for %s, skipping' % doi)
                    else:
                        if len(transform_spec) != len(doi):
                            tlogger.info('Found DOI length mismatch with spec, skipping: %s and %s' % (doi, transform_spec))
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

                            data.update(metadata)

                row = '\t'.join([publisher_id, doi, issn, json.dumps(data)]) + '\n'
                target_file.write(row)

        self.run_pipeline_threads(process_article_rows, article_rows, tlogger=tlogger)

        target_file.close()

        task_args['input_file'] = target_file_name
        task_args['count'] = count

        return task_args
