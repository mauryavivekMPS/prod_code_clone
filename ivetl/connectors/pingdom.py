import time
import requests
import datetime
from ivetl.connectors.base import BaseConnector, MaxTriesAPIError
from ivetl import utils


class PingdomConnector(BaseConnector):
    SERVER = 'https://api.pingdom.com'
    API_PATH = '/api/2.0'

    max_attempts = 7
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

                # pause between attempts to reduce throttling (or whatever), longer for the final two attempts
                if attempt == self.max_attempts - 2:
                    time.sleep(30)
                elif attempt == self.max_attempts - 1:
                    time.sleep(300)
                else:
                    time.sleep(0.2)

                response.raise_for_status()
                success = True
            except requests.HTTPError as http_error:
                if http_error.response.status_code == requests.codes.NOT_FOUND:
                    return {}
                if http_error.response.status_code in (requests.codes.REQUEST_TIMEOUT, requests.codes.UNAUTHORIZED, 524, 403):
                    self._log("Pingdom API timed out. Trying again...")
                    attempt += 1
                elif http_error.response.status_code in (requests.codes.INTERNAL_SERVER_ERROR, requests.codes.BAD_GATEWAY):
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

    def get_check_stats(self, check_id, from_date, to_date):
        uptime_stats = []

        for date in utils.day_range(from_date, to_date):
            from_timestamp = int(date.timestamp())
            to_timestamp = int((date + datetime.timedelta(1)).timestamp())

            self.tlogger.info('Getting stat for %s for %s' % (check_id, date.strftime('%Y-%m-%d')))

            raw_stats = self._get_with_retry(
                '/summary.average/%s' % check_id,
                params={'includeuptime': 'true', 'from': from_timestamp, 'to': to_timestamp}
            )

            uptime_stats.append({
                'date': date,
                'avg_response_ms': raw_stats['summary']['responsetime']['avgresponse'],
                'total_up_sec': raw_stats['summary']['status']['totalup'],
                'total_down_sec': raw_stats['summary']['status']['totaldown'],
                'total_unknown_sec': raw_stats['summary']['status']['totalunknown'],
            })

        return {
            'id': check_id,
            'stats': uptime_stats
        }

    def get_check_details(self, check_id):
        self.tlogger.info('Get stat metadata for %s' % check_id)
        return self._get_with_retry('/checks/%s' % check_id)['check']
