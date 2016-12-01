import csv
import codecs
import json
import re
from ivetl.common import common
from ivetl.celery import app
from ivetl.connectors import CrossrefConnector, DoiProxyConnector, SassConnector
from ivetl.models import PublisherJournal, Doi_Transform_Rule
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
        total_count = task_args['count']

        product = common.PRODUCT_BY_ID[product_id]

        # if cohort product, skip this task
        if product['cohort']:
            tlogger.info("Cohort product - Skipping Task")
            return task_args

        issn_to_hw_journal_code = {j.electronic_issn: j.journal_code for j in PublisherJournal.objects.filter(publisher_id=publisher_id, product_id=product_id)}
        issn_to_hw_journal_code.update({j.print_issn: j.journal_code for j in PublisherJournal.objects.filter(publisher_id=publisher_id, product_id=product_id)})

        target_file_name = work_folder + "/" + publisher_id + "_" + "hwmetadatalookup" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\t'
                          'DOI\t'
                          'ISSN\t'
                          'DATA\n')

        count = 0

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        transform_rules_by_journal_code = {}

        doi_proxy = DoiProxyConnector()
        sass = SassConnector()

        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                if count == 1:
                    continue

                publisher_id = line[0]
                doi = line[1]
                issn = line[2]
                data = json.loads(line[3])

                tlogger.info(str(count-1) + ". Retrieving HW Metadata for: " + doi)

                hw_journal_code = None
                if 'ISSN' in data and (len(data['ISSN']) > 0) and data['ISSN'][0] in issn_to_hw_journal_code:
                    hw_journal_code = issn_to_hw_journal_code[data['ISSN'][0]]

                if not hw_journal_code:
                    tlogger.info("No HW Journal Code for ISSN ... skipping record.")

                else:

                    # check that we have the rules loaded
                    if hw_journal_code not in transform_rules_by_journal_code:
                        rules = Doi_Transform_Rule.objects.filter(journal_code=hw_journal_code, type='hw-doi')
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
                            new_rule = Doi_Transform_Rule.objects.create(
                                journal_code=hw_journal_code,
                                type='hw-doi',
                                match_expression=match_expression,
                                transform_spec=transform_spec,
                            )

                            # whack it in the local cache
                            transform_rules_by_journal_code[hw_journal_code].append(new_rule)

                    if not transform_spec:
                        tlogger.info('Could not find or create a transform spec, skipping record: %s' + doi)
                    else:
                        if len(transform_spec) != len(doi):
                            tlogger.info('Found DOI length mismatch with spec, skipping record: %s and %s' % (doi, transform_spec))
                        else:
                            hw_doi = transform_doi(doi, transform_spec)

                            # try transformed
                            metadata = sass.get_metadata(publisher_id, hw_journal_code, hw_doi, tlogger)

                            # fallback to uppercase
                            if not metadata:
                                metadata = sass.get_metadata(publisher_id, hw_journal_code, doi.upper(), tlogger)

                            # fallback to as-is
                            if not metadata:
                                metadata = sass.get_metadata(publisher_id, hw_journal_code, doi, tlogger)

                            data.update(metadata)

                row = """%s\t%s\t%s\t%s\n""" % (publisher_id, doi, issn, json.dumps(data))
                target_file.write(row)

        target_file.close()

        task_args['input_file'] = target_file_name
        task_args['count'] = count

        return task_args
