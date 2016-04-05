import csv
import codecs
import json
import urllib.parse
import urllib.request
import re
import requests
from requests import HTTPError
from lxml import etree
from ivetl.common import common
from ivetl.celery import app
from ivetl.connectors import CrossrefConnector, DoiProxyConnector
from ivetl.models import Publisher_Journal, Doi_Transform_Rule
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

    return pattern


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

    SASSFS_BASE_URL = 'http://sassfs-index.highwire.org/nlm-pubid/doi?' \
                      'scheme=http%3A%2F%2Fschema.highwire.org%2FPublishing%23role&' \
                      'term=http%3A%2F%2Fschema.highwire.org%2FJournal%2FArticle&'

    SASS_BASE_URL = 'http://sass.highwire.org'

    ISSN_JNL_QUERY_LIMIT = 1000000

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        file = task_args['input_file']
        total_count = task_args['count']

        product = common.PRODUCT_BY_ID[product_id]

        # if cohort product, skip this task
        if product['cohort']:
            tlogger.info("Cohort product - Skipping Task")
            return task_args

        issn_to_hw_journal_code = {j.electronic_issn: j.journal_code for j in Publisher_Journal.objects.filter(publisher_id=publisher_id, product_id=product_id)}
        issn_to_hw_journal_code.update({j.print_issn: j.journal_code for j in Publisher_Journal.objects.filter(publisher_id=publisher_id, product_id=product_id)})

        target_file_name = work_folder + "/" + publisher_id + "_" + "hwmetadatalookup" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\t'
                          'DOI\t'
                          'ISSN\t'
                          'DATA\n')

        count = 0

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        transform_rules_by_journal_code = {}

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
                        # generate a new rule
                        match_expression, transform_spec = generate_doi_transform_rule(doi)

                        # save it to the db
                        new_rule = Doi_Transform_Rule.objects.create(
                            journal_code=hw_journal_code,
                            type='hw-doi',
                            match_expression=match_expression,
                            transform_spec=transform_spec,
                        )

                        # whack it in the local cache
                        transform_rules_by_journal_code[hw_journal_code].append(new_rule)

                    hw_doi = transform_doi(doi, transform_spec)

                    value = urllib.parse.urlencode({'value': hw_doi})
                    url = self.SASSFS_BASE_URL + 'under=/' + hw_journal_code + '&' + value

                    tlogger.info("Looking up HREF on SASSFS:")
                    tlogger.info(url)

                    attempt = 0
                    max_attempts = 3
                    while attempt < max_attempts:
                        try:

                            r = requests.get(url, timeout=30)

                            root = etree.fromstring(r.content)
                            n = root.xpath('//results:results/results:result/results:result-set/results:row/results:atom.href', namespaces=common.ns)

                            if len(n) != 0:
                                href = n[0].text

                                url = self.SASS_BASE_URL + href

                                tlogger.info("Looking up details on SASS:")
                                tlogger.info(url)

                                r = requests.get(url, timeout=30)
                                r.raise_for_status()

                                root = etree.fromstring(r.content)

                                # is open access
                                oa = root.xpath('./nlm:permissions/nlm:license[@license-type="open-access"]', namespaces=common.ns)
                                if len(oa) > 0:
                                    oa = 'Yes'
                                else:
                                    oa = 'No'

                                data['is_open_access'] = oa
                                print(oa)

                                # Article Type
                                article_type = None
                                sub_article_type = None

                                at = root.xpath('./nlm:article-categories/nlm:subj-group[@subj-group-type="leader"]/nlm:subject', namespaces=common.ns)

                                if len(at) == 0:
                                    at = root.xpath('./nlm:article-categories/nlm:subj-group[@subj-group-type="heading"]/nlm:subject', namespaces=common.ns)

                                if len(at) == 0:
                                    at = root.xpath('./nlm:article-categories/nlm:subj-group[@subj-group-type="heading"]//nlm:subj-group[@subj-group-type="display-group"]/nlm:subject[@content-type="original"]', namespaces=common.ns)

                                if len(at) == 0:
                                    at = root.xpath('./nlm:article-categories/nlm:subj-group[@subj-group-type="heading"]//nlm:subj-group[@subj-group-type="display-group"]/nlm:subject[@content-type="display-singular"]', namespaces=common.ns)

                                if len(at) != 0:
                                    article_type = at[0].text
                                    article_type = re.sub("<.*?>", "", article_type)
                                    article_type = article_type.strip(' \t\r\n')
                                    article_type = article_type.replace('\n', ' ')
                                    article_type = article_type.replace('\t', ' ')
                                    article_type = article_type.replace('\r', ' ')
                                    article_type = article_type.title()

                                if len(at) != 0:
                                    sub_at = root.xpath('./nlm:article-categories/nlm:subj-group[@subj-group-type="heading"]/nlm:subj-group[not(@subj-group-type)]/nlm:subject', namespaces=common.ns)

                                    if len(sub_at) == 0:
                                        sub_at = root.xpath('./nlm:article-categories/nlm:subj-group[@subj-group-type="heading"]/nlm:subj-group[not(@subj-group-type)]/nlm:subj-group[@subj-group-type="display-group"]/nlm:subject[@content-type="original"]', namespaces=common.ns)

                                    if len(sub_at) != 0:
                                        sub_article_type = sub_at[0].text
                                        sub_article_type = re.sub("<.*?>", "", sub_article_type)
                                        sub_article_type = sub_article_type.strip(' \t\r\n')
                                        sub_article_type = sub_article_type.replace('\n', ' ')
                                        sub_article_type = sub_article_type.replace('\t', ' ')
                                        sub_article_type = sub_article_type.replace('\r', ' ')
                                        sub_article_type = sub_article_type.title()

                                if publisher_id == 'pnas' or publisher_id == 'rup' and article_type is not None and article_type != '' and sub_article_type is not None and sub_article_type != '':

                                    if publisher_id == 'rup':
                                        article_type = sub_article_type
                                    else:
                                        article_type += ": " + sub_article_type

                                    tlogger.info("Article Type with Sub Type: " + article_type)

                                if article_type is None or article_type == '':
                                    article_type = "None"

                                data['article_type'] = article_type
                                tlogger.info("Article Type: " + article_type)

                                subject_category = None
                                sc = root.xpath('./nlm:article-categories/nlm:subj-group[@subj-group-type="hwp-journal-coll"]/nlm:subject', namespaces=common.ns)

                                if len(sc) != 0:
                                    subject_category = sc[0].text
                                    subject_category = re.sub("<.*?>", "", subject_category)
                                    subject_category = subject_category.strip(' \t\r\n')
                                    subject_category = subject_category.replace('\n', ' ')
                                    subject_category = subject_category.replace('\t', ' ')
                                    subject_category = subject_category.replace('\r', ' ')
                                    subject_category = subject_category.title()

                                if subject_category is None or subject_category == '':
                                    subject_category = "None"

                                data['subject_category'] = subject_category
                                tlogger.info("Subject Category: " + subject_category)

                            else:
                                tlogger.info("No SASS HREF found for DOI: " + doi)

                            break

                        except HTTPError as he:
                            if he.response.status_code == requests.codes.BAD_GATEWAY or he.response.status_code == requests.codes.UNAUTHORIZED or he.response.status_code == requests.codes.REQUEST_TIMEOUT:
                                tlogger.info("HTTP 401/408/502 - HW API failed. Trying Again")
                                attempt += 1
                            else:
                                raise

                        except Exception:
                            tlogger.info("General Exception - HW API failed. Trying Again")
                            attempt += 1

                row = """%s\t%s\t%s\t%s\n""" % (publisher_id, doi, issn, json.dumps(data))

                target_file.write(row)
                target_file.flush()

            tsv.close()

        target_file.close()

        task_args['input_file'] = target_file_name
        task_args['count'] = count

        return task_args
