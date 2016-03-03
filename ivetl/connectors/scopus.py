import requests
import urllib.parse
import urllib.request
from requests import HTTPError
from lxml import etree
from ivetl.common import common
from ivetl.connectors.base import BaseConnector, AuthorizationAPIError, MaxTriesAPIError
from ivetl.connectors.crossref import CrossrefConnector


class ScopusConnector(BaseConnector):
    BASE_SCOPUS_URL_XML = 'http://api.elsevier.com/content/search/index:SCOPUS?httpAccept=application%2Fxml&apiKey='
    BASE_SCOPUS_URL_JSON = 'http://api.elsevier.com/content/search/index:SCOPUS?httpAccept=application%2Fjson&apiKey='
    ABSTRACT_SCOPUS_URL_JSON = 'http://api.elsevier.com/content/abstract/eid/'
    MAX_ATTEMPTS = 10
    REQUEST_TIMEOUT_SECS = 30
    ITEMS_PER_PAGE = 25

    def __init__(self, apikeys):
        self.apikeys = apikeys
        self.count = 0

    def get_entry(self, doi, tlogger, issns=None, volume=None, issue=None, page=None):
        scopus_id = None
        scopus_cited_by_count = None
        has_abstract = True

        attempt = 0
        success = False

        self.count += 1
        url_api = self.BASE_SCOPUS_URL_XML + self.apikeys[self.count % len(self.apikeys)] + '&'

        while not success and attempt < self.MAX_ATTEMPTS:
            try:
                url = url_api + urllib.parse.urlencode({'query': 'doi(' + doi + ')'})

                tlogger.info("Lookup up using doi")
                tlogger.info(url)

                r = requests.get(url, timeout=30)
                r.raise_for_status()

                root = etree.fromstring(r.content, etree.HTMLParser())
                self.check_for_auth_error(root)

                n = root.xpath('//entry/eid', namespaces=common.ns)
                if len(n) == 0 and issns is not None and volume is not None and issue is not None and page is not None:

                    query = ''
                    for i in range(len(issns)):
                        query += 'ISSN(' + issns[i] + ')'
                        if i != len(issns) - 1:
                            query += " OR "

                    query += " AND VOLUME(" + volume + ")"
                    query += " AND issue(" + issue + ")"
                    query += " AND pages(" + page + ")"

                    url = url_api + urllib.parse.urlencode({'query': 'doi(' + doi + ')'})

                    tlogger.info("Looking up using volume/issue/page")
                    tlogger.info(url)

                    r = requests.get(url, timeout=30)
                    r.raise_for_status()

                    root = etree.fromstring(r.content, etree.HTMLParser())
                    self.check_for_auth_error(root)

                    n = root.xpath('//entry/eid', namespaces=common.ns)

                if len(n) != 0:
                    scopus_id = n[0].text

                    c = root.xpath('//entry/citedby-count', namespaces=common.ns)
                    if len(c) != 0:
                        scopus_cited_by_count = c[0].text

                    #Check if article has abstract
                    # abstract_url = self.ABSTRACT_SCOPUS_URL_JSON + scopus_cited_by_count + \
                    #                '?httpAccept=application%2Fjson&apiKey=' + \
                    #                self.apikeys[self.count % len(self.apikeys)]
                    # r = requests.get(abstract_url, timeout=30)
                    # r.raise_for_status()
                    #
                    # has_abstract = False
                    # abstract_data = r.json()
                    #
                    # # if response does not have top tag, assume there is an abstract
                    # if 'abstracts-retrieval-response' not in abstract_data:
                    #     has_abstract = True

                success = True

            except AuthorizationAPIError:
                raise

            except HTTPError as he:
                if he.response.status_code in (requests.codes.NOT_FOUND, requests.codes.UNAUTHORIZED, requests.codes.REQUEST_TIMEOUT, requests.codes.INTERNAL_SERVER_ERROR):
                    tlogger.info("Scopus API failed. Trying again...")
                    attempt += 1
                else:
                    raise

            except:
                tlogger.info("Scopus API failed. Trying Again")
                attempt += 1

        if not success:
            raise MaxTriesAPIError(self.MAX_ATTEMPTS)

        return scopus_id, scopus_cited_by_count

    def get_citations(self, article_scopus_id, is_cohort, tlogger):
        offset = 0
        citations = []

        self.count += 1

        url_api = self.BASE_SCOPUS_URL_JSON + self.apikeys[self.count % len(self.apikeys)] + '&'
        crossref = CrossrefConnector("", "", tlogger)

        while offset != -1:

            attempt = 0
            max_attempts = 5
            r = None
            success = False

            while not success and attempt < max_attempts:
                try:
                    query = 'query=refeid(' + article_scopus_id + ')'

                    url = url_api + query
                    url += '&count=' + str(self.ITEMS_PER_PAGE)
                    url += '&start=' + str(offset)

                    tlogger.info("Searching Scopus: " + url)
                    r = requests.get(url, timeout=30)
                    r.raise_for_status()

                    success = True

                except HTTPError as he:
                    if he.response.status_code == requests.codes.NOT_FOUND or he.response.status_code == requests.codes.UNAUTHORIZED or he.response.status_code == requests.codes.REQUEST_TIMEOUT:
                        tlogger.info("HTTP 401/408 - Scopus API failed. Trying Again")
                        attempt += 1
                    else:
                        raise

                except Exception:
                    tlogger.info("General Exception - Scopus API failed. Trying Again")
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

                            if 'eid' not in scopus_citation or scopus_citation['eid'].strip() == '':
                                continue

                            if 'prism:doi' in scopus_citation and (scopus_citation['prism:doi'] != ''):
                                doi = scopus_citation['prism:doi']
                            else:
                                doi = scopus_citation['eid']

                            scopus_id = None
                            if 'eid' in scopus_citation and (scopus_citation['eid'] != 0):
                                scopus_id = scopus_citation['eid']

                            citation_date = None
                            cr_article = crossref.get_article(doi)

                            if cr_article is None or cr_article['date'] is None:
                                #tlogger.info("Using Scopus value for date of citation")
                                if 'prism:coverDate' in scopus_citation and (scopus_citation['prism:coverDate'] != ''):
                                    citation_date = scopus_citation['prism:coverDate']
                            else:
                                #tlogger.info("Using CrossRef value for date of citation")
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

                            citations.append({
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

                        total_results = int(scopus_data['search-results']['opensearch:totalResults'])
                        if self.ITEMS_PER_PAGE + offset < total_results:
                            offset += self.ITEMS_PER_PAGE
                        else:
                            offset = -1

                else:
                    offset = -1
            else:
                raise MaxTriesAPIError(self.MAX_ATTEMPTS)

        return citations

    @staticmethod
    def check_for_auth_error(root):
        n = root.xpath('//service-error', namespaces=common.ns)
        if len(n) > 0:
            raise AuthorizationAPIError(etree.tostring(root))
