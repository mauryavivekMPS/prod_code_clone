import os
import csv
import codecs
import json
import threading
from ivetl.common import common
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.connectors import MendeleyConnector


@app.task
class MendeleyLookupTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        file = task_args['input_file']
        target_file_name = work_folder + "/" + publisher_id + "_" + "mendeleylookup" + "_" + "target.tab"

        def reader_without_unicode_breaks(f):
            while True:
                yield next(f).replace('\ufeff', '')
                continue

        already_processed = set()

        # if the file exists, read it in assuming a job restart
        if os.path.isfile(target_file_name):
            with codecs.open(target_file_name, encoding='utf-16') as tsv:
                for line in csv.reader(reader_without_unicode_breaks(tsv), delimiter='\t'):
                    if line and len(line) == 3 and line[0] != 'PUBLISHER_ID':
                        manuscript_id = line[1]
                        already_processed.add(manuscript_id)

        if already_processed:
            tlogger.info('Found %s existing items to reuse' % len(already_processed))

        target_file = codecs.open(target_file_name, 'a', 'utf-16')
        if not already_processed:
            target_file.write('\t'.join(['PUBLISHER_ID', 'MANUSCRIPT_ID', 'DATA']) + '\n')

        mendeley = MendeleyConnector(common.MENDELEY_CLIENT_ID, common.MENDELEY_CLIENT_SECRET)

        manuscript_rows = []

        # read everything in from the input file first
        line_count = 0
        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):

                line_count += 1
                if line_count == 1:
                    continue

                manuscript_id = line[1]
                data = json.loads(line[2])

                if manuscript_id in already_processed:
                    continue

                manuscript_rows.append((publisher_id, manuscript_id, data))

        count = 0
        count_lock = threading.Lock()

        total_count = len(manuscript_rows)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        tlogger.info('Total articles to be processed: %s' % total_count)

        def process_manuscript_rows(manuscript_rows_for_this_thread):
            nonlocal count
            thread_article_count = 0

            for article_row in manuscript_rows_for_this_thread:

                with count_lock:
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                thread_article_count += 1

                _, manuscript_id, data = article_row

                if data['status'] == "Match found":
                    tlogger.info(str(count - 1) + ". Retrieving Mendeley saves for: " + manuscript_id)
                    doi = data['xref_doi']

                    try:
                        saves = mendeley.get_saves(doi)
                        tlogger.info('Found %s saves for %s' % (saves, manuscript_id))
                        data['mendeley_saves'] = saves
                    except:
                        tlogger.info("No saves, skipping")
                else:
                    tlogger.info("No match found for %s, skipping" % manuscript_id)

                row = '\t'.join([publisher_id, manuscript_id, json.dumps(data)]) + '\n'
                target_file.write(row)

        self.run_pipeline_threads(process_manuscript_rows, manuscript_rows, tlogger=tlogger)

        target_file.close()

        task_args['count'] = count
        task_args['input_file'] = target_file_name
        return task_args
