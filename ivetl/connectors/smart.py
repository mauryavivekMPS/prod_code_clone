import requests
from ivetl.connectors.base import BaseConnector, MaxTriesAPIError


class SmartConnector(BaseConnector):
    METADATA_URL = 'https://smart.highwire.org/api/cluster.json?environment=production'
    max_attempts = 3
    request_timeout = 300

    def __init__(self, tlogger=None):
        self.tlogger = tlogger

    def get_metadata(self):
        r = self.get_with_retry(self.METADATA_URL)
        return r.json()

    def get_with_retry(self, url):
        attempt = 0
        success = False
        r = None
        while not success and attempt < self.max_attempts:
            try:
                r = requests.get(url, timeout=self.request_timeout)
                r.raise_for_status()
                success = True
            except Exception:
                    self.log("General Exception - Smart API failed. Trying again...")
                    attempt += 1

        if not success:
            raise MaxTriesAPIError(self.max_attempts)

        return r

    def log(self, message):
        if self.tlogger:
            self.tlogger.info(message)
