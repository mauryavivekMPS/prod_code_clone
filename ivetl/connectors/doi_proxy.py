import requests
from bs4 import BeautifulSoup

from ivetl.connectors.base import BaseConnector, MaxTriesAPIError


class DoiProxyConnector(BaseConnector):
    max_attempts = 5
    request_timeout = 30

    def __init__(self, tlogger=None):
        self.tlogger = tlogger

    def get_hw_doi(self, doi):
        # use the dx resolver to get the HW version of the DOI
        url = 'http://dx.doi.org/' + doi
        headers = {'Accept': 'application/vnd.crossref.unixref+xml'}
        r = self.get_with_retry(url, headers=headers)
        soup = BeautifulSoup(r.content, 'xml')
        return soup.find('doi').text

    def get_with_retry(self, url, headers={}):
        attempt = 0
        success = False
        r = None
        while not success and attempt < self.max_attempts:
            try:
                r = requests.get(url, headers=headers, timeout=self.request_timeout)
                r.raise_for_status()
                success = True
            except requests.HTTPError as http_error:
                if http_error.response.status_code == requests.codes.REQUEST_TIMEOUT or http_error.response.status_code == requests.codes.UNAUTHORIZED:
                    self.log("DOI Proxy API timed out. Trying again...")
                    attempt += 1
                elif http_error.response.status_code == requests.codes.INTERNAL_SERVER_ERROR or http_error.response.status_code == requests.codes.BAD_GATEWAY:
                    self.log("DOI Proxy  API 500 error. Trying again...")
                    attempt += 1
                else:
                    raise http_error
            except Exception:
                    self.log("General Exception - DOI Proxy API failed. Trying Again")
                    attempt += 1

        if not success:
            raise MaxTriesAPIError(self.max_attempts)

        return r

    def log(self, message):
        if self.tlogger:
            self.tlogger.info(message)
