import requests
import urllib.parse
import urllib.request
from requests import HTTPError
from lxml import etree
from ivetl.common import common
from ivetl.connectors.base import BaseConnector, AuthorizationAPIError, MaxTriesAPIError
from ivetl.connectors.crossref import CrossrefConnector


class ScopusConnector(BaseConnector):
    BASE_SCOPUS_URL_XML = 'http://10.0.1.47/content/search/scopus?httpAccept=application%2Fxml&apiKey='
    BASE_SCOPUS_URL_JSON = 'http://10.0.1.47/content/search/scopus?httpAccept=application%2Fjson&apiKey='
    MAX_ATTEMPTS = 10
    REQUEST_TIMEOUT_SECS = 30
    RESULTS_PER_PAGE = 25
    MAX_TOTAL_RESULTS = 5000

    def __init__(self, apikeys):
        # self.apikeys = apikeys
        # May 18, 2018
        # hardcoding to single key setup by scopus to temporarily grant access while business contract is being finalized
        self.apikeys = ['8145c7f21e2bd5532da29ff92aefadf6']
        self.count = 0

    def get_entry(self, doi, tlogger, issns=None, volume=None, issue=None, page=None):
        scopus_id = None
        scopus_cited_by_count = None
        scopus_subtype = None

        attempt = 0
        success = False

        self.count += 1
        url_api = self.BASE_SCOPUS_URL_XML + self.apikeys[self.count % len(self.apikeys)] + '&'

        while not success and attempt < self.MAX_ATTEMPTS:
            try:
                url = url_api + urllib.parse.urlencode({'query': 'doi(' + doi + ')'})

                tlogger.info("DOI: {0}, query: {1}".format(doi, url))

                r = requests.get(url, timeout=30)
                r.raise_for_status()

                root = etree.fromstring(r.content, etree.HTMLParser())
                self.check_for_auth_error(root)

                n = root.xpath('//entry/eid', namespaces=common.ns)
                if len(n) == 0 and issns and volume and issue and page:

                    query = ''
                    for i in range(len(issns)):
                        query += 'ISSN(' + issns[i] + ')'
                        if i != len(issns) - 1:
                            query += " OR "

                    query += " AND VOLUME(" + volume + ")"
                    query += " AND issue(" + issue + ")"
                    query += " AND pages(" + page + ")"

                    url = url_api + urllib.parse.urlencode({'query': 'doi(' + doi + ')'})

                    tlogger.info("Searching by volume/issue/page: {}".format(url))

                    r = requests.get(url, timeout=30)
                    r.raise_for_status()

                    root = etree.fromstring(r.content, etree.HTMLParser())
                    self.check_for_auth_error(root)

                    n = root.xpath('//entry/eid', namespaces=common.ns)

                if len(n):
                    scopus_id = n[0].text

                    cited_by_element = root.xpath('//entry/citedby-count', namespaces=common.ns)
                    if len(cited_by_element):
                        scopus_cited_by_count = cited_by_element[0].text

                    subtype_element = root.xpath('//entry/subtypedescription', namespaces=common.ns)
                    if len(subtype_element):
                        scopus_subtype = subtype_element[0].text

                success = True

            except HTTPError as he:
                if he.response.status_code == requests.codes.NOT_FOUND:
                    tlogger.info("DOI {0} not found in the MAG.".format(doi))
                    break
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

        if not success and attempt >= self.MAX_ATTEMPTS:
            raise MaxTriesAPIError(self.MAX_ATTEMPTS)

        return scopus_id, scopus_cited_by_count, scopus_subtype

    def get_citations(self, article_scopus_id, is_cohort, tlogger, should_get_citation_details=None, existing_count=None):
        offset = 0
        citations_to_be_processed = []
        collected_citations = []
        skipped = False
        self.count += 1

        url_api = self.BASE_SCOPUS_URL_JSON + self.apikeys[self.count % len(self.apikeys)] + '&'
        crossref = CrossrefConnector("", "", tlogger)

        num_citations_to_be_processed = 0

        while offset != -1 and offset < self.MAX_TOTAL_RESULTS:

            attempt = 0
            max_attempts = 5
            r = None
            success = False

            while not success and attempt < max_attempts:
                try:
                    query = 'query=refeid(' + article_scopus_id + ')'

                    url = url_api + query
                    url += '&count=' + str(self.RESULTS_PER_PAGE)
                    url += '&start=' + str(offset)

                    tlogger.info("scopus-connector %s: Searching scopus offset %s" % (article_scopus_id, offset))
                    r = requests.get(url, timeout=30)
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
                    cr_article = crossref.get_article(doi)

                    if cr_article is None or cr_article['date'] is None:
                        if 'prism:coverDate' in scopus_citation and (scopus_citation['prism:coverDate'] != ''):
                            citation_date = scopus_citation['prism:coverDate']
                    else:
                        citation_date = cr_article['date'].strftime('%Y-%m-%d')

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
