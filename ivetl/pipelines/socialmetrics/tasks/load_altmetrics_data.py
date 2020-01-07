import csv
import os
import requests

from ivetl import utils
from ivetl.common import common
from ivetl.celery import app
from ivetl.models import AltmetricsSocialData
from ivetl.pipelines.task import Task
from requests.auth import HTTPBasicAuth


@app.task
class LoadAltmetricsDataTask(Task):
    REMOTE_FILE_URL = 'https://www.altmetric.com/dumps/dump.php'
    LOCAL_FILE_ZIPPED_PATH = '/iv/social-metadata/altmetrics.gz'
    LOCAL_FILE_UNZIPPED_PATH = '/iv/social-metadata/altmetrics'
    LOCAL_FILE_RENAMED_PATH = '/iv/social-metadata/altmetrics.tsv'
    USERNAME = 'highwire'
    PASSWORD = ',n9VW/WmGBoA6Z}n.xMCErgjk23'

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        with open(self.LOCAL_FILE_ZIPPED_PATH, 'wb') as f:
            r = requests.get(self.REMOTE_FILE_URL, auth=HTTPBasicAuth(self.USERNAME, self.PASSWORD), stream=True)
            for block in r.iter_content(1024):
                f.write(block)

        tlogger.info('Downloaded new file: %s' % self.LOCAL_FILE_ZIPPED_PATH)

        os.system('gunzip ' + self.LOCAL_FILE_ZIPPED_PATH)
        os.rename(self.LOCAL_FILE_UNZIPPED_PATH, self.LOCAL_FILE_RENAMED_PATH)
        tlogger.info('Unzipped and renamed to: %s' % self.LOCAL_FILE_RENAMED_PATH)

        total_count = utils.file_len(self.LOCAL_FILE_RENAMED_PATH) - 1  # ignore the header
        tlogger.info('Found %s records' % total_count)

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0
        with open(self.LOCAL_FILE_RENAMED_PATH, encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                if not row['DOI']:
                    continue

                AltmetricsSocialData.objects(doi=common.normalizedDoi(row['DOI'])).update(
                    altmetrics_id=row['ID'],
                    facebook=row['FACEBOOK_WALLS'],
                    blogs=row['BLOGS'],
                    twitter=row['TWITTER_ACCOUNTS'],
                    gplus=row['GPLUS_ACCOUNTS'],
                    news_outlets=row['NEWS_OUTLETS'],
                    wikipedia=row['WIKIPEDIA'],
                    video=row['VIDEO'],
                    policy_docs=row['POLICY_DOCS'],
                    reddit=row['REDDIT'],
                )

        task_args['count'] = total_count

        return task_args
