import requests
import requests.exceptions
import time
import json
from bs4 import BeautifulSoup
from datetime import datetime
from ivetl.connectors.base import BaseConnector, MaxTriesAPIError, AuthorizationAPIError
from ivetl.common import common


class CrossrefConnector(BaseConnector):
    BASE_URL = 'https://api.crossref.org'
    BASE_CITATION_URL = 'https://doi.crossref.org'

    connector_name = 'Crossref'
    max_attempts = 5
    request_timeout = 120 
    request_timeout_multiplier = 1.1

    def __init__(self, username=None, password=None, tlogger=None):
        self.username = username
        self.password = password
        self.tlogger = tlogger

    def get_citations(self, doi):
        url = self.BASE_CITATION_URL + '/servlet/getForwardLinks?usr=%s&pwd=%s&doi=%s&format=unixsd' % (self.username, self.password, doi)
        response_text = self.get_with_retry(url)
        soup = BeautifulSoup(response_text, 'xml')
        citations = [e.text for e in soup.find_all('doi', type="journal_article")]
        return citations

    def get_example_doi_for_journal(self, issn):
        url = self.BASE_URL + '/works?mailto=nmehta@highwire.org&filter=issn:' % issn
        response_text = self.get_with_retry(url)
        first_doi = json.loads(response_text)['message']['items'][0]['DOI']
        return first_doi

    def get_journal_info(self, issn, year):
        journal = None

        try:
            journal_response_url = self.BASE_URL + '/journals/' + issn + "?mailto=nmehta@highwire.org"
            journal_response_text = self.get_with_retry(journal_response_url)
            journal_response_json = json.loads(journal_response_text)

            journal_name = journal_response_json['message']['title']
            publisher_name = journal_response_json['message']['publisher']

            works_url = self.BASE_URL + "/works?mailto=nmehta@highwire.org&rows=1&filter=issn:%s,from-pub-date:%s-01-01,until-pub-date:%s-12-31" % (issn, year, year)
            works_response_text = self.get_with_retry(works_url)

            works_response_json = json.loads(works_response_text)
            article_count = works_response_json['message']['total-results']

            journal = {
                'name': journal_name,
                'publisher': publisher_name,
                'article_count': article_count
            }

        except ValueError:
            pass

        return journal

    def get_article(self, doi):
        url = self.BASE_URL + '/works/' + doi + "?mailto=nmehta@highwire.org"
        article_response_text = self.get_with_retry(url)

        try:
            article_json = json.loads(article_response_text)
        except (ValueError, TypeError):
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
            if 'issue' in article_json and article_json['issue']:
                if type(article_json['issue']) is list:
                    issue = article_json['issue'][0]
                else:
                    issue = article_json.get('issue', None)
            else:
                issue = None

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
            if 'page' in article_json and article_json['page']:
                if type(article_json['page']) is list:
                    pages = article_json['page'][0]
                else:
                    pages = article_json.get('page', None)
            else:
                pages = None

            # title
            if 'title' in article_json and type(article_json['title']) is list and article_json['title']:
                title = article_json['title'][0]
            else:
                title = None

            # volume
            if 'volume' in article_json and article_json['volume']:
                if type(article_json['volume']) is list:
                    volume = article_json['volume'][0]
                else:
                    volume = article_json.get('volume', None)
            else:
                volume = None

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
        title_search_term = title

        if use_generic_query_param:
            url = self.BASE_URL + '/works?mailto=nmehta@highwire.org&rows=30&filter=from-pub-date:%s,type:journal-article&query=%s' % (
                date_search_term,
                title_search_term,
            )
        else:
            url = self.BASE_URL + '/works?mailto=nmehta@highwire.org&rows=30&filter=from-pub-date:%s,type:journal-article&query.title=%s' % (
                date_search_term,
                title_search_term,
            )

            if authors:
                url += '&query.author=%s' % ' '.join(authors)

        self.log('search url: %s' % url)

        search_response_text = self.get_with_retry(url)

        try:
            search_results_json = json.loads(search_response_text)
        except (ValueError, TypeError):
            search_results_json = None

        return search_results_json

    def get_with_retry_direct(self, url):
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
                self.check_for_auth_error(r.text)
                success = True
            except requests.HTTPError as http_error:
                status = http_error.response.status_code
                if status == requests.codes.NOT_FOUND:
                    return r
                if status == requests.codes.REQUEST_TIMEOUT:
                    self.log("Crossref API timed out. Trying again...")
                    _pause_for_retry()
                    attempt += 1
                elif status == requests.codes.UNAUTHORIZED:
                    self.log("Crossref API 401 UNAUTHORIZED error. Skipping DOI lookup...")
                    return r
                elif status == requests.codes.INTERNAL_SERVER_ERROR or status == requests.codes.BAD_GATEWAY:
                    self.log("Crossref API 500 error. Trying again...")
                    _pause_for_retry()
                    attempt += 1
                elif status == requests.codes.TOO_MANY_REQUESTS:
                    self.log("Crossref API 427 TOO MANY REQUESTS error. Trying again...")
                    _pause_for_retry()
                    attempt += 1
                else:
                    raise http_error
            except Exception:
                    self.log("General Exception - CrossRef API failed. Trying again..." + url)
                    _pause_for_retry()
                    attempt += 1

        if not success:
            raise MaxTriesAPIError(self.max_attempts)

        return r.text

    def get_with_retry(self, url, timeout=None, timeout_multiplier=None):
        attempt = 0
        success = False

        if timeout is None:
            timeout = self.request_timeout
        if timeout_multiplier is None:
            timeout_multiplier = self.request_timeout_multiplier

        def _pause_for_retry():
            if attempt == self.max_attempts - 3:
                time.sleep(30)
            elif attempt == self.max_attempts - 2:
                time.sleep(300)
            elif attempt == self.max_attempts - 1:
                time.sleep(600)
            else:
                time.sleep(0.2)

        response_status_code = None
        response_text = None
        while not success and attempt < self.max_attempts:
            limit_request = {
                'type': 'GET',
                'service': 'crossref',
                'url': url,
                'timeout': timeout,
            }

            completed_response = False

            try:
                r = requests.post('http://' + common.RATE_LIMITER_SERVER + '/limit', json=limit_request, timeout=self.request_timeout)
                r.raise_for_status()

                limit_response = r.json()
                if limit_response.get('limit_status', 'error') == 'ok':
                    response_status_code = limit_response['status_code']
                    response_text = limit_response['text']
                    completed_response = True

            except requests.exceptions.ReadTimeout as e:
                old_timeout = timeout
                timeout *= timeout_multiplier
                self.log("Crossref API timed out (%d). Increasing timeout to %d and trying again..." % (old_timeout, timeout))
                _pause_for_retry()
                attempt += 1
                continue
            except (requests.exceptions.RequestException, ValueError) as e:
                self.log("Exception encountered on attempt #%d for %s: %s" % ((attempt+1), url, e))
                _pause_for_retry()
                attempt += 1
                continue

            if completed_response:
                if response_status_code == requests.codes.REQUEST_TIMEOUT:
                    old_timeout = timeout
                    timeout *= timeout_multiplier
                    self.log("Crossref API timed out (%d). Increasing timeout to %d and trying again..." % (old_timeout, timeout))
                    _pause_for_retry()
                    attempt += 1
                elif response_status_code == requests.codes.UNAUTHORIZED:
                    self.log("Crossref API 401 UNAUTHORIZED error. Skipping lookup...")
                    self.check_for_auth_error(response_text)
                    continue
                elif response_status_code in (requests.codes.INTERNAL_SERVER_ERROR, requests.codes.BAD_GATEWAY):
                    self.log("Crossref API 500 error. Trying again...")
                    _pause_for_retry()
                    attempt += 1
                else:
                    self.check_for_auth_error(response_text)
                    success = True

            else:
                self.log('Unexpected response from the rate limiter. Trying again...')
                _pause_for_retry()
                attempt += 1

        if not success:
            raise MaxTriesAPIError(self.max_attempts)

        return response_text

    def log(self, message, exc_info=None):
        if self.tlogger:
            self.tlogger.info(message, exc_info=exc_info)

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
            return '%s-%s-%s' % (parts[0], parts[1], parts[2])

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

    def check_for_auth_error(self, response_text):
        if 'Incorrect password for username' in response_text:
            self.log("Crossref API incorrect password.")
            raise AuthorizationAPIError(response_text)

        if 'not authorized to view references' in response_text:
            self.log("Crossref API 401 UNAUTHORIZED error.")
            raise AuthorizationAPIError(response_text)

