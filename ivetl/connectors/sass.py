import re
import requests
import urllib.parse
import urllib.request
from requests import HTTPError
from lxml import etree
from ivetl.common import common
from ivetl.connectors.base import BaseConnector


class SassConnector(BaseConnector):
    MAX_ATTEMPTS = 3

    SASSFS_BASE_URL = 'http://sassfs-index.highwire.org/nlm-pubid/doi?' \
                      'scheme=http%3A%2F%2Fschema.highwire.org%2FPublishing%23role&' \
                      'term=http%3A%2F%2Fschema.highwire.org%2FJournal%2FArticle&'

    SASS_BASE_URL = 'http://sass.highwire.org'

    ISSN_JNL_QUERY_LIMIT = 1000000

    def __init__(self, tlogger=None):
        self.tlogger = tlogger

    def get_metadata(self, publisher_id, hw_journal_code, hw_doi, tlogger=None):
        value = urllib.parse.urlencode({'value': hw_doi})
        url = self.SASSFS_BASE_URL + 'under=/' + hw_journal_code + '&' + value

        tlogger.info("Looking up HREF on SASSFS:")
        tlogger.info(url)

        metadata = {}

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

                    if r.status_code == 404:
                        tlogger.info('404 Not Found response from SASS for %s, skipping...' % href)
                    else:
                        r.raise_for_status()

                        root = etree.fromstring(r.content)

                        # is open access
                        oa = root.xpath('./nlm:permissions/nlm:license[@license-type="open-access"]', namespaces=common.ns)
                        if len(oa) > 0:
                            oa = 'Yes'
                        else:
                            oa = 'No'
                        metadata['is_open_access'] = oa

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

                        metadata['article_type'] = article_type
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

                        metadata['subject_category'] = subject_category
                        tlogger.info("Subject Category: " + subject_category)

                else:
                    tlogger.info("No SASS HREF found for DOI: " + hw_doi)

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

        return metadata

    def _log(self, message):
        if self.tlogger:
            self.tlogger.info(message)
        else:
            print(message)