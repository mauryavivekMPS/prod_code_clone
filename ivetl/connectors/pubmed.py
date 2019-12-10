import json
import re
import requests
import requests.exceptions
import urllib

from ivetl.connectors.base import BaseConnector, MaxTriesAPIError, AuthorizationAPIError
from ivetl.common import common

class PubMedConnector(BaseConnector):
    connector_name = 'PubMed'
    max_attempts = 5
    request_timeout = 120
    request_timeout_multiplier = 1.1
    citation_search_base = ('https://eutils.ncbi.nlm.nih.gov/'
        'entrez/eutils/esearch.fcgi?db=pubmed&api_key={0}'
        '&retmode=json&term=').format(common.NCBI_API_KEY)

    def __init__(self, tlogger=None):
        self.tlogger = tlogger

    def log(self, message, exc_info=None):
        if self.tlogger:
            self.tlogger.info(message, exc_info=exc_info)
        else:
            print(message)

    def citation_lookup_url(self, publication):
        url = self.citation_search_base
        terms = []
        journal = None
        volume = None
        issue = None
        fpage = None
        if 'container-title' in publication:
            try:
                journal = publication['container-title'][0]
                journal = re.sub(r'[][)(}{]+', '', journal)
                journal = re.sub(' ', '+', journal)
                terms.append('{0}%5BJour%5D'.format(journal))
            except IndexError:
                self.log(('Unexpected format for journal title: '
                '{0}').format(publication['container']))
        elif 'ISSN' in publication:
            try:
                journal = publication['ISSN'][0]
                terms.append('{0}%5BJour%5D'.format(journal))
            except IndexError:
                self.log(('Unexpected format for ISSN: '
                    '{0}').format(publication['ISSN']))
        if 'volume' in publication:
            volume = publication['volume']
            volume = re.sub(' ', '+', volume)
            terms.append('{0}%5Bvolume%5D'.format(volume))
        if 'issue' in publication:
            issue = publication['issue']
            issue = re.sub(' ', '+', issue)
            terms.append('{0}%5Bissue%5D'.format(issue))
        elif ('journal-issue' in publication and
            'issue' in publication['journal-issue']):
            issue = publication['journal-issue']['issue']
            issue = re.sub(' ', '+', issue)
            terms.append('{0}%5Bissue%5D'.format(issue))
        if 'page' in publication:
            pages = publication['page'].split('-')
            fpage = pages[0]
            terms.append('{0}%5Bpage%5D'.format(fpage))
        # to definitively find a given publication, and not a peer publication,
        # we want all of the following metadata
        # note issue is not required; some journals publish issue-less volumes
        if journal and volume and fpage:
            term = '+AND+'.join(terms)
            url += term
            return url
        return None

    def doi_lookup_url(self, doi):
        url = self.citation_search_base
        term = urllib.parse.quote(doi, safe='')
        url += term
        return url

    def override(self, publication):
        # VIZOR-224, override if not found in PubMed
        url = self.citation_lookup_url(publication)
        try:
            if url:
                result = self.check_citation(url)
                return not result
            elif 'DOI' in publication:
                doi = publication['DOI']
                url = self.doi_lookup_url(doi)
                result = self.check_doi(url, doi)
                return not result
            else:
                self.log('Failed to generate PubMed lookup URL for publication.')
                return False
        except Exception:
            # if lookup fails, default to no override to prevent false positives
            return False

    def check_citation(self, url):
        result = self.search_single_citation(url)
        count = 0
        if 'esearchresult' in result and 'count' in result['esearchresult']:
            count = result['esearchresult']['count']
            try:
                count = int(count)
            except ValueError:
                self.log(('Non-Integer count value received from PubMed lookup: '
                    '{0}, {1}').format(count, url))
                raise
        if count > 0:
            return True
        return False

    def check_doi(self, url, doi):
        result = self.search_single_citation(url)
        querytranslation = '{0}[All Fields]'.format(doi)
        count = 0
        if ('esearchresult' in result and
            'querytranslation' in result['esearchresult'] and
            result['esearchresult']['querytranslation'] == querytranslation and
            'count' in result['esearchresult']):
            count = result['esearchresult']['count']
            try:
                count = int(count)
            except ValueError:
                self.log(('Non-Integer count value received from PubMed lookup: '
                    '{0}, {1}').format(count, url))
                raise
        if count > 0:
            return True
        return False

    def search_single_citation(self, url):

        try:
            response_text = self.ratelimit_with_retry(url, 'pubmed')
        except MaxTriesAPIError:
            self.log('MaxTriesAPIError for url: {0}'.format(url))
            raise
        except Exception as inst:
            self.log(('Exception encountered for url: {0}, '
                '{1}').format(url, inst))
            raise
        try:
            result = json.loads(response_text)
        except Exception as inst:
            self.log('Failed to parse JSON response for url: {0}', url)
            raise
        return result

    def ratelimit_with_retry(self, url, service=None, timeout=None,
        timeout_multiplier=None):
        # todo: this code mostly duplicates get_with_retry from crossref.py
        # better would be to move it into the base.py connector
        # and have crossref.py and pubmed.py share the same function
        # however that will require some refactoring and more testing
        # various other connectors implement their own get_with_retry
        if not service:
            m = 'service required in ratelimit_with_retry for url: %s' % url
            raise Exception(m)

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
                'service': service,
                'url': url,
                'timeout': timeout,
            }

            completed_response = False

            try:
                r = requests.post('http://' + common.RATE_LIMITER_SERVER +
                    '/limit', json=limit_request, timeout=timeout)
                r.raise_for_status()

                limit_response = r.json()
                if limit_response.get('limit_status', 'error') == 'ok':
                    response_status_code = limit_response['status_code']
                    response_text = limit_response['text']
                    completed_response = True

            except requests.exceptions.ReadTimeout as e:
                old_timeout = timeout
                timeout *= timeout_multiplier
                self.log(('{0} API timed out ({1}). '
                    'Increasing timeout to {2} and '
                    'trying again...').format(service, old_timeout, timeout))
                _pause_for_retry()
                attempt += 1
                continue
            except (requests.exceptions.RequestException, ValueError) as e:
                self.log(('Exception encountered on {0} attempt #{1} for {2}: '
                    '{3}').format(service, (attempt+1), url, e))
                _pause_for_retry()
                attempt += 1
                continue

            if completed_response:
                if response_status_code == requests.codes.REQUEST_TIMEOUT:
                    old_timeout = timeout
                    timeout *= timeout_multiplier
                    self.log(('{0} API timed out ({1}). Increasing timeout '
                        'to {2} and trying again'
                        '...').format(service, old_timeout, timeout))
                    _pause_for_retry()
                    attempt += 1
                elif response_status_code == requests.codes.UNAUTHORIZED:
                    self.log(('{0} API 401 UNAUTHORIZED error. '
                        'Skipping lookup...').format(service))
                    # self.check_for_auth_error(response_text)
                    continue
                elif response_status_code in (
                    requests.codes.INTERNAL_SERVER_ERROR,
                    requests.codes.BAD_GATEWAY):
                    self.log(('{0} API 500 error. '
                        'Trying again...').format(service))
                    _pause_for_retry()
                    attempt += 1
                else:
                    # self.check_for_auth_error(response_text)
                    success = True

            else:
                self.log(('Unexpected response from the rate limiter. '
                    'Trying again...'))
                _pause_for_retry()
                attempt += 1

        if not success:
            raise MaxTriesAPIError(self.max_attempts)

        return response_text
