import csv
import os
import requests
from requests.auth import HTTPBasicAuth
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import AltmetricsSocialData


@app.task
class LoadAltmetricsDataTask(Task):
    REMOTE_FILE_URL = 'https://dl.dropboxusercontent.com/u/17066303/altmetrics-small-example.txt'
    LOCAL_FILE_PATH = '/iv/social-metadata/altmetrics.tsv'
    USERNAME = 'highwire'
    PASSWORD = ',n9VW/WmGBoA6Z}n.xMCErgjk23'

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        with open(self.LOCAL_FILE_PATH, 'wb') as f:
            r = requests.get(self.REMOTE_FILE_URL, auth=HTTPBasicAuth(self.USERNAME, self.PASSWORD), stream=True)
            for block in r.iter_content(1024):
                f.write(block)

        # need to set permissions on file because of s3 fuse
        os.system('chmod +r ' + self.LOCAL_FILE_PATH)

        tlogger.info('Downloaded new file: %s' % self.LOCAL_FILE_PATH)

        # count lines
        total_count = 0
        with open(self.LOCAL_FILE_PATH, 'r') as f:
            for line in f.readlines():
                total_count += 1

        # ignore the header
        total_count -= 1

        tlogger.info('Found %s records' % total_count)

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0
        with open(self.LOCAL_FILE_PATH) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                if not row['DOI']:
                    continue

                AltmetricsSocialData.objects(doi=row['DOI']).update(
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

        return {
            'count': count
        }
