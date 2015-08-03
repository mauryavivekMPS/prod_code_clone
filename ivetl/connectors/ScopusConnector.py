from __future__ import absolute_import
import urllib.parse
import urllib.request
import traceback

import requests
from requests import HTTPError
from lxml import etree

from ivetl.common import common
from ivetl.connectors import AuthorizationAPIError
from ivetl.connectors import MaxTriesAPIError


class ScopusConnector():


    BASE_SCOPUS_URL_XML = 'http://api.elsevier.com/content/search/index:SCOPUS?httpAccept=application%2Fxml&apiKey='
    BASE_SCOPUS_URL_JSON = 'http://api.elsevier.com/content/search/index:SCOPUS?httpAccept=application%2Fjson&apiKey='

    MAX_ATTEMPTS = 3
    REQUEST_TIMEOUT_SECS = 30
    ITEMS_PER_PAGE = 25

    def __init__(self, apikey):
        self.apikey = apikey

    def getScopusEntry(self, doi, issns, volume, issue, page, tlogger):

        scopus_id = None
        scopus_cited_by_count = None

        attempt = 0
        success = False

        url_api = self.BASE_SCOPUS_URL_XML + self.apikey + '&'

        while not success and attempt < self.MAX_ATTEMPTS:
            try:

                url = url_api + urllib.parse.urlencode({'query': 'doi(' + doi + ')'})

                tlogger.info("Lookup up using doi")
                tlogger.info(url)

                r = requests.get(url, timeout=30)
                #sleep(2)

                root = etree.fromstring(r.content, etree.HTMLParser())
                self.checkForAuthorizationErrorXML(root)

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

                    root = etree.fromstring(r.content, etree.HTMLParser())
                    self.checkForAuthorizationErrorXML(root)

                    n = root.xpath('//entry/eid', namespaces=common.ns)

                if len(n) != 0:
                    scopus_id = n[0].text

                    c = root.xpath('//entry/citedby-count', namespaces=common.ns)

                    if len(c) != 0:
                        scopus_cited_by_count = c[0].text

                success = True

            except AuthorizationAPIError:
                raise

            except Exception:

                tlogger.info("Scopus API failed. Trying Again")
                traceback.print_exc()

                attempt += 1

        if not success:
            raise MaxTriesAPIError(self.MAX_ATTEMPTS)

        return scopus_id, scopus_cited_by_count


    def getScopusCitations(self, article_scopus_id, tlogger):

        offset = 0
        num_citations = 0
        citations = []

        url_api = self.BASE_SCOPUS_URL_JSON + self.apikey + '&'

        while offset != -1:

            attempt = 0
            max_attempts = 5
            r = None
            success = False
            scopusdata = None

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

                except HTTPError:
                    raise

                except Exception:
                    attempt += 1
                    tlogger.warning("Error connecting to Scopus API.  Trying again.")

            if success:

                scopusdata = r.json()

                if 'search-results' not in scopusdata:
                    offset = -1

                elif 'entry' in scopusdata['search-results'] and len(scopusdata['search-results']['entry']) > 0:

                    if 'error' in scopusdata['search-results']['entry'][0]:
                        offset = -1
                    else:

                        for i in scopusdata['search-results']['entry']:
                            citations.append(i)

                        total_results = int(scopusdata['search-results']['opensearch:totalResults'])
                        if self.ITEMS_PER_PAGE + offset < total_results:
                            offset += self.ITEMS_PER_PAGE
                        else:
                            offset = -1

                else:
                    offset = -1
            else:
                raise MaxTriesAPIError(self.MAX_ATTEMPTS)

        return citations


    def checkForAuthorizationErrorXML(self, root):

        n = root.xpath('//service-error', namespaces=common.ns)
        if len(n) > 0:
            raise AuthorizationAPIError(etree.tostring(root))

