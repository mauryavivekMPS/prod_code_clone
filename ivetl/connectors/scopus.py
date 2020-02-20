import requests
import os
from urllib.parse import quote_plus
from requests import HTTPError
from lxml import etree
#from datetime import datetime
from time import sleep
from ivetl.common import common
from ivetl.connectors.base import BaseConnector, AuthorizationAPIError, MaxTriesAPIError


class ScopusConnector(BaseConnector):
    MAGRESOLVER_IP = os.environ.get('IVETL_MAGRESOLVER_IP', '10.0.1.47')
    MAGRESOLVER_URL_XML = 'http://' + MAGRESOLVER_IP + '/search?doi={0}'
    MAGRESOLVER_URL_JSON = 'http://' + MAGRESOLVER_IP + '/search?paperid={0}&count={1}&start={2}'
    MAX_ATTEMPTS = 3
    REQUEST_TIMEOUT_SECS = 30
    RESULTS_PER_PAGE = 25
    MAX_TOTAL_RESULTS = 5000

    def __init__(self, apikeys=None):
        self.apikeys = apikeys
        self.count = 0

    def get_entry(self, doi, tlogger, issns=None, volume=None, issue=None, page=None):
        """ Get the MAG paper_id for a given DOI.

        Called from scopus_id_lookup.py in the ScopusIdLookupTask pipeline task.
        Called from scopus_citation_lookup.py in ScopusCitationLookupTask.
        """

        scopus_id = None
        scopus_cited_by_count = None
        scopus_subtype = None

        if issns or volume or issue or page:
            tlogger.warning("Search by ISSNs/volume/issue/page not available.")

        attempt = 0
        self.count += 1

        while attempt < self.MAX_ATTEMPTS:
            try:
                url = self.MAGRESOLVER_URL_XML.format(quote_plus(doi))

                tlogger.info("DOI: {0}, query: {1}".format(doi, url))

                r = requests.get(url, timeout = self.REQUEST_TIMEOUT_SECS)
                r.raise_for_status()

                root = etree.fromstring(r.content, etree.HTMLParser())
                self.check_for_auth_error(root)

                node = root.xpath('//entry/eid', namespaces=common.ns)

                if node:
                    scopus_id = node[0].text

                    cited_by_element = root.xpath('//entry/citedby-count', namespaces=common.ns)
                    if len(cited_by_element):
                        scopus_cited_by_count = cited_by_element[0].text

                    subtype_element = root.xpath('//entry/subtypedescription', namespaces=common.ns)
                    if len(subtype_element):
                        scopus_subtype = subtype_element[0].text

                    return scopus_id, scopus_cited_by_count, scopus_subtype

            except HTTPError as he:
                if he.response.status_code == requests.codes.NOT_FOUND:
                    tlogger.info("DOI {0} not found in the MAG.".format(doi))
                    # Return blank for not found in the MAG
                    return None, None, None

                elif he.response.status_code in (requests.codes.TOO_MANY_REQUESTS,
                                               requests.codes.REQUEST_TIMEOUT,
                                               requests.codes.INTERNAL_SERVER_ERROR):
                    tlogger.info("DOI {0} MAG {1.status_code} error, retrying...".format(doi, he.response))
                    attempt += 1
                else:
                    tlogger.info("DOI {0} MAG {1.status_code} error...".format(doi, he.response))
                    raise

            except ConnectionError:
                tlogger.info("MAG API connection error. Retrying.")
                attempt += 1

            except Exception as e:
                tlogger.error("MAG API exception: {0}".format(e))
                tlogger.info("General exception, retrying DOI: {0}".format(doi))
                attempt += 1

            # sleep between retries, before raising MaxTriesAPIError after MAX_ATTEMPTS
            sleep(1)

        raise MaxTriesAPIError(self.MAX_ATTEMPTS)


    def get_citations(self, article_scopus_id, is_cohort, tlogger, should_get_citation_details=None, existing_count=None):
        """ Get the citations for a given MAG paper_id.

        Called from get_scopus_article_citations.py in the GetScopusArticleCitations task.
        """
        offset = 0
        citations_to_be_processed = []
        collected_citations = []
        skipped = False
        self.count += 1

        num_citations_to_be_processed = 0

        while offset != -1 and offset < self.MAX_TOTAL_RESULTS:

            attempt = 0
            r = None
            success = False

            while not success and attempt < self.MAX_ATTEMPTS:
                try:
                    url = self.MAGRESOLVER_URL_JSON.format(article_scopus_id, self.RESULTS_PER_PAGE, offset)

                    tlogger.info("scopus-connector %s: Searching MAG offset %s" % (article_scopus_id, offset))
                    r = requests.get(url, timeout = self.REQUEST_TIMEOUT_SECS)
                    r.raise_for_status()

                    success = True

                except HTTPError as he:
                    if he.response.status_code == requests.codes.NOT_FOUND:
                        tlogger.info("MAG PaperId {0} not found.".format(article_scopus_id))
                        # break
                        skipped = True
                        return collected_citations, num_citations_to_be_processed, skipped
                    elif he.response.status_code in (requests.codes.TOO_MANY_REQUESTS,
                                                    requests.codes.REQUEST_TIMEOUT,
                                                    requests.codes.INTERNAL_SERVER_ERROR):
                        tlogger.info("MAG PaperId error {1.status_code}, retrying...".format(article_scopus_id,
                                                                                             he.response))
                        attempt += 1
                    else:
                        tlogger.info("MAG PaperId error {1.status_code}...".format(article_scopus_id, he.response))
                        raise

                except Exception as e:
                    tlogger.error("MAG API exception: {0}".format(e))
                    tlogger.info("General exception, retrying PaperId: {0}".format(article_scopus_id))
                    attempt += 1

            if success:
                scopus_data = r.json()

                if 'search-results' not in scopus_data:
                    offset = -1

                elif 'entry' in scopus_data['search-results'] and len(scopus_data['search-results']['entry']) > 0:

                    if 'error' in scopus_data['search-results']['entry'][0]:
                        offset = -1
                    else:

                        for scopus_citation in scopus_data['search-results']['entry']:

                            # skip records with invalid IDs
                            if 'eid' not in scopus_citation or scopus_citation['eid'].strip() == '':
                                continue

                            if 'prism:doi' in scopus_citation and (scopus_citation['prism:doi'] != ''):
                                doi = scopus_citation['prism:doi']
                            else:
                                doi = scopus_citation['eid']

                            # skip for strange or null values (including the weird lists we sometimes get from scopus)
                            if not doi or type(doi) == list:
                                tlogger.info('scopus-connector %s: Citation has an invalid DOI, skipping' % article_scopus_id)
                                continue

                            citations_to_be_processed.append(scopus_citation)

                        total_results = int(scopus_data['search-results']['opensearch:totalResults'])
                        if self.RESULTS_PER_PAGE + offset < total_results:
                            offset += self.RESULTS_PER_PAGE
                        else:
                            offset = -1

                else:
                    offset = -1
            else:
                raise MaxTriesAPIError(self.MAX_ATTEMPTS)

            num_citations_to_be_processed = len(citations_to_be_processed)
            tlogger.info('scopus-connector %s: Found %s citations' % (article_scopus_id, num_citations_to_be_processed))
            if not existing_count or (existing_count and existing_count != num_citations_to_be_processed):
                skipped = False

                for scopus_citation in citations_to_be_processed:

                    if 'prism:doi' in scopus_citation and (scopus_citation['prism:doi'] != ''):
                        doi = scopus_citation['prism:doi']
                    else:
                        doi = scopus_citation['eid']

                    if should_get_citation_details:
                        if not should_get_citation_details(doi):
                            tlogger.info('scopus-connector %s: We already have details for %s, skipping' % (article_scopus_id, doi))
                            continue

                    scopus_id = None
                    if 'eid' in scopus_citation and (scopus_citation['eid'] != 0):
                        scopus_id = scopus_citation['eid']

                    citation_date = None
                    if 'prism:coverDate' in scopus_citation:
                        #citation_date = datetime.strptime(scopus_citation['prism:coverDate'], '%Y-%m-%d')
                        citation_date = scopus_citation['prism:coverDate'] 

                    first_author = None
                    if 'dc:creator' in scopus_citation and (scopus_citation['dc:creator'] != 0):
                        first_author = scopus_citation['dc:creator']

                    issue = None
                    if 'prism:issueIdentifier' in scopus_citation and (scopus_citation['prism:issueIdentifier'] != 0):
                        issue = scopus_citation['prism:issueIdentifier']

                    journal_issn = None
                    if 'prism:issn' in scopus_citation and (scopus_citation['prism:issn'] != 0):
                        journal_issn = scopus_citation['prism:issn']

                    journal_title = None
                    if 'prism:publicationName' in scopus_citation and (scopus_citation['prism:publicationName'] != 0):
                        journal_title = scopus_citation['prism:publicationName']

                    pages = None
                    if 'prism:pageRange' in scopus_citation and (scopus_citation['prism:pageRange'] != 0):
                        pages = scopus_citation['prism:pageRange']

                    title = None
                    if 'dc:title' in scopus_citation and (scopus_citation['dc:title'] != 0):
                        title = scopus_citation['dc:title']

                    volume = None
                    if 'prism:volume' in scopus_citation and (scopus_citation['prism:volume'] != 0):
                        volume = scopus_citation['prism:volume']

                    collected_citations.append({
                        'doi': doi,
                        'scopus_id': scopus_id,
                        'date': citation_date,
                        'first_author': first_author,
                        'issue': issue,
                        'journal_issn': journal_issn,
                        'journal_title': journal_title,
                        'pages': pages,
                        'title': title,
                        'volume': volume,
                        'source': 'Scopus',
                        'is_cohort': is_cohort
                    })
            else:
                skipped = True

        return collected_citations, num_citations_to_be_processed, skipped

    @staticmethod
    def check_for_auth_error(root):
        n = root.xpath('//service-error', namespaces=common.ns)
        if len(n) > 0:
            raise AuthorizationAPIError(etree.tostring(root))
