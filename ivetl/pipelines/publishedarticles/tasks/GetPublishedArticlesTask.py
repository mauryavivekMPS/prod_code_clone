import codecs
import json
import requests
from requests import HTTPError
from ivetl.celery import app
from ivetl.pipelines.task import Task


@app.task
class GetPublishedArticlesTask(Task):

    ISSNS = 'GetPublishedArticlesTask.ISSNs'
    START_PUB_DATE = 'GetPublishedArticlesTask.StartPubDate'
    WORK_FOLDER = 'GetPublishedArticlesTask.WorkFolder'

    def run_task(self, publisher_id, product_id, job_id, work_folder, tlogger, task_args):

        issns = task_args[GetPublishedArticlesTask.ISSNS]
        start_publication_date = task_args[GetPublishedArticlesTask.START_PUB_DATE]
        from_pub_date_str = start_publication_date.strftime('%Y-%m-%d')

        target_file_name = work_folder + "/" + publisher_id + "_" + "xrefpublishedarticles" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\t'
                          'DOI\t'
                          'ISSN\t'
                          'DATA\n')

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
                            tlogger.info("HTTP 401/408 - Scopus API failed. Trying Again")
                            attempt += 1

                            if attempt >= max_attempts:
                                raise
                        else:
                            raise
                    except Exception:
                        tlogger.info("General Exception - Scopus API failed. Trying Again")

                        attempt += 1
                        if attempt >= max_attempts:
                            raise

                xrefdata = r.json()

                if 'ok' in xrefdata['status'] and len(xrefdata['message']['items']) > 0:

                    for i in xrefdata['message']['items']:

                        row = """%s\t%s\t%s\t%s\n""" % (
                            publisher_id,
                            i['DOI'],
                            issn,
                            json.dumps(i))

                        target_file.write(row)
                        target_file.flush()

                        count += 1

                    offset += task_args['articles_per_page']

                else:
                    offset = -1

        target_file.close()

        task_args[self.INPUT_FILE] = target_file_name
        task_args[self.COUNT] = count

        return task_args








