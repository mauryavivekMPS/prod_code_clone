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

        attempt = 0
        success = False
        hw_doi = None
        while not success and attempt < self.max_attempts:
            try:
                r = requests.get(url, headers=headers, timeout=self.request_timeout)
                r.raise_for_status()

                soup = BeautifulSoup(r.content, 'xml')

                doi_element = soup.find('doi')

                if not doi_element:
                    self.log('DOI Proxy return a seemlingly valid response, but no DOI is found. Trying again...')
                    self.log(r.content)
                    self.log('Trying again...')
                    attempt += 1
                else:
                    hw_doi = doi_element.text
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

        return hw_doi

    def log(self, message):
        if self.tlogger:
            self.tlogger.info(message)
