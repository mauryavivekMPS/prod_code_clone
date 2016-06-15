import os
import requests
from bs4 import BeautifulSoup
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import F1000SocialData


@app.task
class LoadF1000DataTask(Task):
    REMOTE_FILE_URL = 'https://dl.dropboxusercontent.com/u/17066303/f1000-small-example.xml'
    LOCAL_FILE_PATH = '/iv/social-metadata/f1000.xml'

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        with open(self.LOCAL_FILE_PATH, 'wb') as f:
            r = requests.get(self.REMOTE_FILE_URL, stream=True)
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

        # ignore opening and closing element
        total_count -= 2

        tlogger.info('Found %s records' % total_count)

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0
        with open(self.LOCAL_FILE_PATH) as f:

            for line in f.readlines():

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                # ignore opening and closing elements
                if 'ObjectList' in line:
                    continue

                soup = BeautifulSoup(line, 'xml')

                doi_element = soup.find('Doi')
                if not doi_element:
                    continue

                doi = doi_element.text
                if not doi:
                    continue

                f1000_id = soup.find('Id').text

                try:
                    total_score = int(soup.find('TotalScore').text)
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

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id)

        return {
            'count': count
        }
