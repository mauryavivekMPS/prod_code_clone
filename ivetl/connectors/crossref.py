import traceback
import requests
from bs4 import BeautifulSoup
from ivetl.connectors.base import BaseConnector, MaxTriesAPIError, AuthorizationAPIError


class CrossrefConnector(BaseConnector):
    BASE_CITATION_URL = 'https://doi.crossref.org/servlet/getForwardLinks'
    BASE_ARTICLE_URL = 'http://api.crossref.org/works/'

    connector_name = 'Crossref'
    max_attempts = 3
    request_timeout = 30

    def __init__(self, username, password, tlogger):
        self.username = username
        self.password = password
        self.tlogger = tlogger

    def get_citations(self, doi):
        url = '%s?usr=%s&pwd=%s&doi=%s&format=unixsd' % (self.BASE_CITATION_URL, self.username, self.password, doi)
        r = self.get_with_retry(url)
        soup = BeautifulSoup(r.content, 'xml')
        citations = [e.text for e in soup.find_all('doi')]
        return citations

    def get_article(self, doi):
        url = '%s%s' % (self.BASE_ARTICLE_URL, doi)
        r = self.get_with_retry(url)

        try:
            article_json = r.json()
        except ValueError:
            article_json = None

        article = None

        if article_json:
            article_json = article_json['message']

            # date
            citation_date = self.date_string_from_parts(article_json['issued']['date-parts'])

            # author
            author_parts = article_json['author'][0]
            author = '%s,%s' % (author_parts['family'], author_parts['given'])

            # issue
            issue = article_json.get('issue', None)

            # journal ISSN
            if 'ISSN' in article_json:
                journal_issn = article_json['ISSN'][0]
            else:
                journal_issn = None

            # journal title
            journal_title = article_json['title'][0]

            # pages
            pages = article_json['page']

            # title
            title = article_json['container-title']

            # volume
            volume = article_json.get('volume', None)

            article = {
                'doi': doi,
                'date': citation_date,
                'first_author': author,
                'issue': issue,
                'journal_issn': journal_issn,
                'journal_title': journal_title,
                'pages': pages,
                'title': title,
                'volume': volume,
                'source': 'Crossref',
            }

        return article

    def get_with_retry(self, url):
        attempt = 0
        success = False
        r = None
        while not success and attempt < self.max_attempts:
            try:
                r = requests.get(url, timeout=self.request_timeout)
                r.raise_for_status()
                self.check_for_auth_error(r)
                success = True
            except requests.HTTPError as http_error:
                if http_error.response.status_code == requests.codes.REQUEST_TIMEOUT:
                    self.tlogger.info("Crossref API timed out. Trying again...")
                    attempt += 1
                else:
                    raise http_error

        if not success:
            raise MaxTriesAPIError(self.max_attempts)

        return r

    def date_string_from_parts(self, date_parts_list):
        if type(date_parts_list) is list:
            if len(date_parts_list) == 1 and type(date_parts_list[0]) is list:
                date_parts = date_parts_list[0]
                if date_parts:
                    num_parts = len(date_parts)
                    if num_parts >= 3:
                        parts = date_parts[:3]
                    elif num_parts == 2:
                        parts = date_parts[:2] + [1]
                    elif num_parts == 1:
                        parts = date_parts[:1] + [1, 1]

        if parts:
            return '%s-%s-%s' % tuple(parts)

        return None

    def check_for_auth_error(self, r):
        if 'Incorrect password for username' in r.text:
            raise AuthorizationAPIError(r.text)
