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
                    if line and len(line) == 4 and line[0] != 'PUBLISHER_ID':
                        doi = line[1]
                        already_processed.add(doi)

        if already_processed:
            tlogger.info('Found %s existing items to reuse' % len(already_processed))

        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\tDOI\tISSN\tDATA\n')

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
                doi = line[1]
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

                tlogger.info('Starting on article %s' % doi)

                tlogger.info(str(count - 1) + ". Retrieving Mendelez saves for: " + doi)

                new_saves_value = None
                try:
                    new_saves_value = mendeley.get_saves(doi)
                except:
                    tlogger.info("General Exception - Mendeley API failed for %s. Moving to next article..." % doi)

                if new_saves_value:
                    data['mendeley_saves'] = new_saves_value

                row = """%s\t%s\t%s\t%s\n""" % (publisher_id, doi, issn, json.dumps(data))

                target_file.write(row)

        num_threads = 10
        num_per_thread = round(total_count / num_threads)
        threads = []
        for i in range(num_threads):

            from_index = i * num_per_thread
            if i == num_threads - 1:
                to_index = total_count
            else:
                to_index = (i + 1) * num_per_thread

            tlogger.info('Starting thread for [%s:%s]' % (from_index, to_index))

            new_thread = threading.Thread(target=process_article_rows, args=(article_rows[from_index:to_index],))
            new_thread.start()
            threads.append(new_thread)

        for thread in threads:
            tlogger.info('Waiting on thread: %s' % thread)
            thread.join()

        target_file.close()

        task_args['input_file'] = target_file_name
        task_args['count'] = count

        return task_args
