import codecs
import json
import requests
from requests import HTTPError
from ivetl.celery import app
from ivetl.common import common
from ivetl.pipelines.task import Task


@app.task
class GetPublishedArticlesTask(Task):

    ISSNS = 'GetPublishedArticlesTask.ISSNs'
    START_PUB_DATE = 'GetPublishedArticlesTask.StartPubDate'
    WORK_FOLDER = 'GetPublishedArticlesTask.WorkFolder'

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        issns = task_args[GetPublishedArticlesTask.ISSNS]
        start_publication_date = task_args[GetPublishedArticlesTask.START_PUB_DATE]
        from_pub_date_str = start_publication_date.strftime('%Y-%m-%d')

        target_file_name = work_folder + "/" + publisher_id + "_" + "xrefpublishedarticles" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\t'
                          'DOI\t'
                          'ISSN\t'
                          'DATA\n')

        articles = {}
        count = 0
        for issn in issns:

            offset = 0

            while offset != -1:

                attempt = 0
                max_attempts = 3
                r = None
                success = False

                if 'max_articles_to_process' in task_args and task_args['max_articles_to_process'] and count >= task_args['max_articles_to_process']:
                    break

                while not success and attempt < max_attempts:
                    try:
                        url = 'http://api.crossref.org/journals/' + issn + '/works'
                        url += '?rows=' + str(task_args['articles_per_page'])
                        url += '&offset=' + str(offset)
                        url += '&filter=type:journal-article,from-pub-date:' + from_pub_date_str

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

                        # # Use this only for testing!!
                        if count > 30:
                            break

                    offset += task_args['articles_per_page']

                else:
                    offset = -1

        for a in articles.values():
            row = """%s\t%s\t%s\t%s\n""" % (
                            publisher_id,
                            a[0],
                            a[1],
                            a[2])

            target_file.write(row)

        target_file.close()

        task_args['input_file'] = target_file_name
        task_args['count'] = count

        return task_args








