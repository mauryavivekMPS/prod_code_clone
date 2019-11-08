import os
import requests

from bs4 import BeautifulSoup
from ivetl import utils
from ivetl.common import common
from ivetl.celery import app
from ivetl.models import F1000SocialData
from ivetl.pipelines.task import Task


@app.task
class LoadF1000DataTask(Task):
    REMOTE_FILE_URL = 'http://linkout.export.f1000.com.s3.amazonaws.com/linkout/intermediate.xml'
    LOCAL_FILE_PATH = '/iv/social-metadata/f1000.xml'

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        with open(self.LOCAL_FILE_PATH, 'wb') as f:
            r = requests.get(self.REMOTE_FILE_URL, stream=True)
            for block in r.iter_content(1024):
                f.write(block)

        # need to set permissions on file because of s3 fuse
        os.system('chmod +r ' + self.LOCAL_FILE_PATH)
        tlogger.info('Downloaded new file: %s' % self.LOCAL_FILE_PATH)

        total_count = utils.file_len(self.LOCAL_FILE_PATH) - 2  # ignore opening and closing element
        tlogger.info('Found %s records' % total_count)

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0
        with open(self.LOCAL_FILE_PATH, encoding='utf-8') as f:

            for line in f.readlines():

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                # ignore opening and closing elements
                if 'ObjectList' in line:
                    continue

                soup = BeautifulSoup(line, 'xml')

                doi_element = soup.find('Doi')
                if not doi_element:
                    continue

                doi = common.normalizedDoi(doi_element.text)
                if not doi:
                    continue

                f1000_id_element = soup.find('Id')
                if not f1000_id_element:
                    continue

                f1000_id = f1000_id_element.text
                if not f1000_id:
                    continue

                total_score_element = soup.find('TotalScore')
                if not total_score_element:
                    continue

                try:
                    total_score = int(total_score_element.text)
                except ValueError:
                    total_score = 0

                num_recommendations = len(soup.findAll('RecommendationDate'))
                if num_recommendations:
                    average_score = total_score / num_recommendations
                else:
                    average_score = 0.0

                F1000SocialData.objects(doi=doi).update(
                    f1000_id=f1000_id,
                    total_score=total_score,
                    num_recommendations=num_recommendations,
                    average_score=average_score,
                )

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, tlogger, show_alerts=task_args['show_alerts'])

        task_args['count'] = total_count

        return task_args
