import codecs
import json
import requests
import urllib.parse
from requests import HTTPError
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.common import common


@app.task
class GetPublishedArticlesTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        issns = task_args['issns']
        from_pub_date_str = self.from_json_date(task_args['start_pub_date']).strftime('%Y-%m-%d')

        target_file_name = work_folder + "/" + publisher_id + "_" + "xrefpublishedarticles" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\tDOI\tISSN\tDATA\n')

        articles = {}
        count = 0

        issns = ['0006-4971']
        for issn in issns:

            more_results = True
            cursor = '*'

            while more_results:

                attempt = 0
                max_attempts = 3
                r = None
                success = False

                if 'max_articles_to_process' in task_args and task_args['max_articles_to_process'] and count >= task_args['max_articles_to_process']:
                    break

                while not success and attempt < max_attempts:
                    try:
                        encoded_params = urllib.parse.urlencode({
                            'rows': task_args['articles_per_page'],
                            'cursor': cursor,
                            'filter': 'type:journal-article,from-pub-date:%s' % from_pub_date_str,
                        })

                        url = 'http://api.crossref.org/journals/%s/works?%s' % (issn, encoded_params)

                        tlogger.info("Searching CrossRef for: " + url)
                        r = requests.get(url, timeout=30)
                        r.raise_for_status()

                        success = True

                    except HTTPError as he:
                        if he.response.status_code == requests.codes.UNAUTHORIZED or he.response.status_code == requests.codes.REQUEST_TIMEOUT:
                            tlogger.info("HTTP 401/408 - CrossRef API failed. Trying Again")
                            attempt += 1

                            if attempt >= max_attempts:
                                raise
                        else:
                            raise
                    except Exception:
                        tlogger.info("General Exception - CrossRef API failed. Trying Again")

                        attempt += 1
                        if attempt >= max_attempts:
                            raise

                xrefdata = r.json()

                total_count = len(xrefdata['message']['items'])

                if 'ok' in xrefdata['status'] and total_count > 0:

                    self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

                    for i in xrefdata['message']['items']:

                        articles[i['DOI']] = (i['DOI'], issn, json.dumps(i))
                        count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                        if common.DEBUG_QUICKLY:
                            if count > 3:
                                break

                    cursor = xrefdata['message']['next-cursor']

                else:
                    more_results = False

        for a in articles.values():
            row = "%s\t%s\t%s\t%s\n" % (publisher_id, a[0], a[1], a[2])
            target_file.write(row)

        target_file.close()

        task_args['input_file'] = target_file_name
        task_args['count'] = count

        return task_args








