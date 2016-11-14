import re
import requests
import time
from bs4 import BeautifulSoup
from datetime import datetime

from ivetl.connectors.base import BaseConnector, MaxTriesAPIError, AuthorizationAPIError


class CrossrefConnector(BaseConnector):
    BASE_CITATION_URL = 'https://doi.crossref.org/servlet/getForwardLinks'
    BASE_ARTICLE_URL = 'http://api.crossref.org/works'
    BASE_WORKS_URL = 'http://api.crossref.org/journals/%s/works'
    BASE_JNL_URL = 'http://api.crossref.org/journals/%s'

    connector_name = 'Crossref'
    max_attempts = 7
    request_timeout = 30

    def __init__(self, username=None, password=None, tlogger=None):
        self.username = username
        self.password = password
        self.tlogger = tlogger

    def get_citations(self, doi):
        url = '%s?usr=%s&pwd=%s&doi=%s&format=unixsd' % (self.BASE_CITATION_URL, self.username, self.password, doi)
        r = self.get_with_retry(url)
        soup = BeautifulSoup(r.content, 'xml')
        citations = [e.text for e in soup.find_all('doi', type="journal_article")]
        return citations

    def get_example_doi_for_journal(self, issn):
        url = self.BASE_WORKS_URL % issn
        r = self.get_with_retry(url)
        first_doi = r.json()['message']['items'][0]['DOI']
        return first_doi

    def get_journal_info(self, issn, year):
        url = self.BASE_JNL_URL % issn
        #print(url)
        r = self.get_with_retry(url)

        journal = None

        try:
            if r.json():
                jnl_name = r.json()['message']['title']
                publisher_name = r.json()['message']['publisher']

                url = self.BASE_JNL_URL % issn + "/works?rows=1&filter=from-pub-date:" + str(year) + \
                      "-01-01,until-pub-date:" + str(year) + "-12-31"

                #print(url)
                r = self.get_with_retry(url)

                article_count = r.json()['message']['total-results']

                journal = {
                    'name': jnl_name,
                    'publisher': publisher_name,
                    'article_count': article_count
                }
        except ValueError:
            pass

        return journal

    def get_article(self, doi):
        url = '%s/%s' % (self.BASE_ARTICLE_URL, doi)
        r = self.get_with_retry(url)

        try:
            article_json = r.json()
        except ValueError:
            article_json = None

        article = None

        if article_json:
            article_json = article_json['message']

            # date
            if 'issued' in article_json:
                citation_date = self.datetime_from_parts(article_json['issued']['date-parts'][0])
            else:
                citation_date = None

            # author
            if 'author' in article_json:
                author_parts = article_json['author'][0]
                author = '%s,%s' % (author_parts.get('family', ''), author_parts.get('given', ''))
            else:
                author = None

            # issue
            issue = article_json.get('issue', None)

            # journal ISSN
            if 'ISSN' in article_json:
                journal_issn = article_json['ISSN'][0]
            else:
                journal_issn = None

            # journal title
            if 'container-title' in article_json and type(article_json['container-title']) is list and article_json['container-title']:
                journal_title = article_json['container-title'][0]
            else:
                journal_title = None

            # pages
            pages = article_json.get('page', None)

            # title
            if 'title' in article_json and type(article_json['title']) is list and article_json['title']:
                title = article_json['title'][0]
            else:
                title = None

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

    def search_article(self, publish_date, title, authors=None, use_generic_query_param=False):
        date_search_term = publish_date.strftime('%Y-%m')
        title_search_term = self.solr_encode(title)

        if use_generic_query_param:
            url = '%s?rows=30&filter=from-pub-date:%s&query=%s' % (
                self.BASE_ARTICLE_URL,
                date_search_term,
                title_search_term,
            )
        else:
            url = '%s?rows=30&filter=from-pub-date:%s&query.title=%s' % (
                self.BASE_ARTICLE_URL,
                date_search_term,
                title_search_term,
            )

            if authors:
                url += '&query.author=%s' % self.solr_encode(' '.join(authors))

        self.log('search url: %s' % url)

        r = self.get_with_retry(url)

        try:
            search_results_json = r.json()
        except ValueError:
            search_results_json = None

        return search_results_json

    def get_with_retry(self, url):
        attempt = 0
        success = False
        r = None

        def _pause_for_retry():
            if attempt == self.max_attempts - 3:
                time.sleep(30)
            elif attempt == self.max_attempts - 2:
                time.sleep(300)
            elif attempt == self.max_attempts - 1:
                time.sleep(600)
            else:
                time.sleep(0.2)

        while not success and attempt < self.max_attempts:
            try:
                r = requests.get(url, timeout=self.request_timeout)
                r.raise_for_status()
                self.check_for_auth_error(r)
                success = True
            except requests.HTTPError as http_error:
                if http_error.response.status_code == requests.codes.NOT_FOUND:
                    return r
                if http_error.response.status_code == requests.codes.REQUEST_TIMEOUT or http_error.response.status_code == requests.codes.UNAUTHORIZED:
                    self.log("Crossref API timed out. Trying again...")
                    _pause_for_retry()
                    attempt += 1
                elif http_error.response.status_code == requests.codes.INTERNAL_SERVER_ERROR or http_error.response.status_code == requests.codes.BAD_GATEWAY:
                    self.log("Crossref API 500 error. Trying again...")
                    _pause_for_retry()
                    attempt += 1
                else:
                    raise http_error
            except Exception:
                    self.log("General Exception - CrossRef API failed. Trying again...")
                    _pause_for_retry()
                    attempt += 1

        if not success:
            raise MaxTriesAPIError(self.max_attempts)

        return r

    def log(self, message):
        if self.tlogger:
            self.tlogger.info(message)

    def date_string_from_parts(self, date_parts_list):
        parts = None
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

    def datetime_from_parts(self, date_parts):
        year = date_parts[0]

        if year is None:
            return None

        month = 1
        if len(date_parts) >= 2:
            month = date_parts[1]

        day = 1
        if len(date_parts) >= 3:
            day = date_parts[2]

        return datetime(year, month, day)

    def check_for_auth_error(self, r):
        if 'Incorrect password for username' in r.text:
            raise AuthorizationAPIError(r.text)

    def solr_encode(self, url_fragment):
        return url_fragment.replace(' ', '+')\
            .replace(':', '\\:')\
            .replace('-', '\\-')\
            .replace('!', '\\!')\
            .replace('(', '\\(')\
            .replace(')', '\\)')\
            .replace('^', '\\^')\
            .replace('[', '\\[')\
            .replace(']', '\\]')\
            .replace('\"', '\\\"')\
            .replace('{', '\\{')\
            .replace('}', '\\}')\
            .replace('~', '\\~')\
            .replace('*', '\\*')\
            .replace('?', '\\?')\
            .replace('|', '\\|')\
            .replace('&', '')\
            .replace(';', '\\;')\
            .replace('/', '\\/')
