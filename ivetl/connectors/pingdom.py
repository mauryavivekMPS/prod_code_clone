import time
import requests
import datetime
from ivetl.connectors.base import BaseConnector, MaxTriesAPIError


class PingdomConnector(BaseConnector):
    SERVER = 'https://api.pingdom.com'
    API_PATH = '/api/2.0'

    max_attempts = 5
    request_timeout = 30

    def __init__(self, email, password, api_key, tlogger=None):
        self.email = email
        self.password = password
        self.api_key = api_key
        self.base_url = self.SERVER + self.API_PATH
        self.tlogger = tlogger

    def _get_with_retry(self, path, params={}):
        attempt = 0
        success = False
        response = None
        while not success and attempt < self.max_attempts:
            try:
                response = requests.get(self.base_url + path, auth=(self.email, self.password), headers={'App-Key': self.api_key}, params=params)
                response.raise_for_status()
                success = True
            except requests.HTTPError as http_error:
                if http_error.response.status_code == requests.codes.NOT_FOUND:
                    return {}
                if http_error.response.status_code == requests.codes.REQUEST_TIMEOUT or http_error.response.status_code == requests.codes.UNAUTHORIZED:
                    self._log("Pingdom API timed out. Trying again...")
                    attempt += 1
                elif http_error.response.status_code == requests.codes.INTERNAL_SERVER_ERROR or http_error.response.status_code == requests.codes.BAD_GATEWAY:
                    self._log("Pingdom API 500 error. Trying again...")
                    attempt += 1
                else:
                    raise http_error
            except Exception:
                    self._log("General Exception - Pingdom API failed. Trying again...")
                    attempt += 1

        if not success:
            raise MaxTriesAPIError(self.max_attempts)

        if response:
            return response.json()
        else:
            return {}

    def _log(self, message):
        if self.tlogger:
            self.tlogger.info(message)
        else:
            print(message)

    def get_checks(self):
        return self._get_with_retry('/checks')['checks']

    def get_check_details_and_uptime(self, check_id, from_date, to_date):

        # get check details
        check_details_with_uptime = self._get_with_retry('/checks/%s' % check_id)['check']

        # to prevent the API from throttling us
        time.sleep(0.2)

        # get uptime stats for the given date range
        uptime_stats = []

        def _date_range(start_date, end_date):
            for n in range(int((end_date - start_date).days)):
                yield start_date + datetime.timedelta(n)

        for date in _date_range(from_date, to_date):
            from_timestamp = int(date.timestamp())
            to_timestamp = int((date + datetime.timedelta(1)).timestamp())

            raw_stats = self._get_with_retry(
                '/summary.average/%s' % check_id,
                params={'includeuptime': 'true', 'from': from_timestamp, 'to': to_timestamp}
            )

            self._log('getting stat %s for %s' % (check_id, date))

            uptime_stats.append({
                'date': date,
                'avg_response_ms': raw_stats['summary']['responsetime']['avgresponse'],
                'total_up_sec': raw_stats['summary']['status']['totalup'],
                'total_down_sec': raw_stats['summary']['status']['totaldown'],
                'total_unknown_sec': raw_stats['summary']['status']['totalunknown'],
            })

        check_details_with_uptime['stats'] = uptime_stats

        return check_details_with_uptime
