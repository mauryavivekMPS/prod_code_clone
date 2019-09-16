import codecs
import json
import urllib.parse
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.connectors import CrossrefConnector
from ivetl.common import common
from ivetl.models import PublisherMetadata


@app.task
class GetPublishedArticlesTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        from_date = self.from_json_date(task_args['from_date'])

        tlogger.info('got date: %s' % from_date)

        issns = task_args['issns']
        publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)
        crossref = CrossrefConnector(publisher.crossref_username, publisher.crossref_password, tlogger)

        target_file_name = work_folder + "/" + publisher_id + "_" + "xrefpublishedarticles" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\tDOI\tISSN\tDATA\n')

        articles = {}
        count = 0

        for issn in issns:

            more_results = True
            cursor = '*'

            while more_results:

                if 'max_articles_to_process' in task_args and task_args['max_articles_to_process'] and count >= task_args['max_articles_to_process']:
                    break

                encoded_params = urllib.parse.urlencode({
                    'rows': task_args['articles_per_page'],
                    'cursor': cursor,
                    'filter': 'issn:%s,type:journal-article,from-pub-date:%s' % (issn, from_date),
                })

                url = 'https://api.crossref.org/works?%s' % encoded_params

                tlogger.info("Searching CrossRef for: " + url)
                response_text = crossref.get_with_retry(url)
                xrefdata = json.loads(response_text)

                total_count = len(xrefdata['message']['items'])

                if 'ok' in xrefdata['status'] and total_count > 0:

                    self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

                    for i in xrefdata['message']['items']:

                        # avoid really big (unused) "reference" element
                        if 'reference' in i:
                            del i['reference']

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








