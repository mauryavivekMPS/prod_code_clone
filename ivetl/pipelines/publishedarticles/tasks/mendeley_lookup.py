import codecs
import csv
import json
import os
import threading

from ivetl.celery import app
from ivetl.common import common
from ivetl.connectors import MendeleyConnector
from ivetl.pipelines.task import Task


@app.task
class MendeleyLookupTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        file = task_args['input_file']
        target_file_name = work_folder + "/" + publisher_id + "_" + "mendeleylookup" + "_" + "target.tab"

        already_processed = set()

        # if the file exists, read it in assuming a job restart
        if os.path.isfile(target_file_name):
            with codecs.open(target_file_name, encoding='utf-16') as tsv:
                for line in csv.reader(self.reader_without_unicode_breaks(tsv), delimiter='\t'):
                    if line and len(line) == 4 and line[0] != 'PUBLISHER_ID':
                        doi = common.normalizedDoi(line[1])
                        already_processed.add(doi)

        if already_processed:
            tlogger.info('Found %s existing items to reuse' % len(already_processed))

        target_file = codecs.open(target_file_name, 'a', 'utf-16')
        if not already_processed:
            target_file.write('\t'.join(['PUBLISHER_ID', 'DOI', 'ISSN', 'DATA']) + '\n')

        mendeley = MendeleyConnector(common.MENDELEY_CLIENT_ID, common.MENDELEY_CLIENT_SECRET)

        article_rows = []

        # read everything in from the input file first
        line_count = 0
        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):

                line_count += 1
                if line_count == 1:
                    continue

                publisher_id = line[0]
                doi = common.normalizedDoi(line[1])
                issn = line[2]
                data = json.loads(line[3])

                if doi in already_processed:
                    continue

                article_rows.append((doi, issn, data))

        count = 0
        count_lock = threading.Lock()

        total_count = len(article_rows)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        tlogger.info('Total articles to be processed: %s' % total_count)

        def process_article_rows(article_rows_for_this_thread):
            nonlocal count

            thread_article_count = 0

            for article_row in article_rows_for_this_thread:
                with count_lock:
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                thread_article_count += 1

                doi, issn, data = article_row

                tlogger.info("Retrieving Mendeley for: %s" % doi)

                new_saves_value = None
                try:
                    new_saves_value = mendeley.get_saves(doi)
                except:
                    tlogger.info("General Exception - Mendeley API failed for %s. Skipping" % doi)

                if new_saves_value:
                    data['mendeley_saves'] = new_saves_value

                row = '\t'.join([publisher_id, doi, issn, json.dumps(data)]) + '\n'
                target_file.write(row)

        self.run_pipeline_threads(process_article_rows, article_rows, tlogger=tlogger)

        target_file.close()

        task_args['input_file'] = target_file_name
        task_args['count'] = count

        return task_args
