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

    def get_metadata(self, publisher_id, hw_journal_code, hw_doi):
        value = urllib.parse.urlencode({'value': hw_doi})
        url = self.SASSFS_BASE_URL + 'under=/' + hw_journal_code + '&' + value

        self._log("Looking up HREF on SASSFS:")
        self._log(url)

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

                    self._log("Looking up details on SASS:")
                    self._log(url)

                    r = requests.get(url, timeout=30)

                    if r.status_code == 404:
                        self._log('404 Not Found response from SASS for %s, skipping...' % href)
                    else:
                        r.raise_for_status()

                        root = etree.fromstring(r.content)

                        # set open access if license_type lists 'open-access' or for rup check ali tagging.
                        open_access = 'No'
                        if publisher_id == 'rup':
                            free_to_read_element = root.xpath('./nlm:permissions/ali:free_to_read[not(@start_date)]', namespaces=common.ns)
                            if free_to_read_element:
                                open_access = 'Yes'
                        else:
                            open_access_element = root.xpath('./nlm:permissions/nlm:license[@license-type="open-access"]', namespaces=common.ns)
                            if open_access_element:
                                open_access = 'Yes'

                        metadata['is_open_access'] = open_access

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

                        if (publisher_id == 'pnas' or publisher_id == 'rup' or publisher_id == 'sfn') and article_type and sub_article_type:

                            if publisher_id == 'rup':
                                article_type = sub_article_type
                            else:
                                article_type += ": " + sub_article_type

                            self._log("Article Type with Sub Type: " + article_type)

                        if article_type is None or article_type == '':
                            article_type = "None"

                        metadata['article_type'] = article_type
                        self._log("Article Type: " + article_type)

                        subject_category = None
                        sc = root.xpath('./nlm:article-categories/nlm:subj-group[@subj-group-type="hwp-journal-coll"]/nlm:subject', namespaces=common.ns)

                        if len(sc) != 0:
                            subject_category = sc[0].text
                            subject_category = re.sub("<.*?>", "", subject_category)
                            subject_category = subject_category.strip()
                            subject_category = subject_category.replace('\n', ' ')
                            subject_category = subject_category.replace('\t', ' ')
                            subject_category = subject_category.replace('\r', ' ')
                            subject_category = subject_category.title()

                        if subject_category is None or subject_category == '':
                            subject_category = "None"

                        metadata['subject_category'] = subject_category
                        self._log("Subject Category: " + subject_category)

                        volume_element = root.xpath('./nlm:volume', namespaces=common.ns)
                        if volume_element:
                            metadata['volume'] = volume_element[0].text

                        self._log('volume value = %s' % metadata.get('volume'))

                        issue_element = root.xpath('./nlm:issue', namespaces=common.ns)
                        if issue_element:
                            metadata['issue'] = issue_element[0].text

                        self._log('issue value = %s' % metadata.get('issue'))

                        fpage_element = root.xpath('./nlm:fpage', namespaces=common.ns)
                        if fpage_element:
                            fpage = fpage_element[0].text
                        else:
                            fpage = None

                        lpage_element = root.xpath('./nlm:lpage', namespaces=common.ns)
                        if lpage_element:
                            lpage = lpage_element[0].text
                        else:
                            lpage = None

                        if fpage:
                            if lpage:
                                metadata['page'] = fpage + '-' + lpage
                            else:
                                metadata['page'] = fpage

                        self._log('page value = %s' % metadata.get('page'))

                else:
                    self._log("No SASS HREF found for DOI: " + hw_doi)

                break

            except HTTPError as he:
                if he.response.status_code == requests.codes.BAD_GATEWAY or he.response.status_code == requests.codes.UNAUTHORIZED or he.response.status_code == requests.codes.REQUEST_TIMEOUT:
                    self._log("HTTP 401/408/502 - HW API failed. Trying Again")
                    attempt += 1
                else:
                    raise

            except Exception:
                self._log("General Exception - HW API failed. Trying Again")
                attempt += 1

        return metadata

    def _log(self, message):
        if self.tlogger:
            self.tlogger.info(message)
        else:
            print(message)
