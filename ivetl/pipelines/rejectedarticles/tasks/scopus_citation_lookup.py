import os
import csv
import codecs
import json
import threading
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.connectors.base import MaxTriesAPIError
from ivetl.connectors.scopus import ScopusConnector
from ivetl.models import PublisherMetadata


@app.task
class ScopusCitationLookupTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        file = task_args['input_file']
        total_count = task_args['count']

        target_file_name = work_folder + "/" + publisher_id + "_" + "scopuscitationlookup" + "_" + "target.tab"

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

        publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)
        mag = ScopusConnector(publisher.scopus_api_keys)

        manuscript_rows = []

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

                manuscript_rows.append((manuscript_id, data))

        count = 0
        count_lock = threading.Lock()

        total_count = len(manuscript_rows)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        tlogger.info('Total manuscripts to be processed: %s' % total_count)

        def process_manuscript_rows(manuscript_rows_for_this_thread):
            nonlocal count

            thread_article_count = 0

            for article_row in manuscript_rows_for_this_thread:
                with count_lock:
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                thread_article_count += 1

                manuscript_id, data = article_row

                if data['status'] == "Match found":
                    doi = data['xref_doi']
                    tlogger.info("Retrieving citations count for manuscript %s, DOI %s" % (manuscript_id, doi))
                    mag_paper_id = None
                    try:
                        mag_paper_id, mag_citations, subtype = mag.get_entry(doi, tlogger)
                    except MaxTriesAPIError:
                        tlogger.info("MAG API failed, trying again")
                        data['citation_lookup_status'] = "Scopus API failed"
                        data['scopus_id'] = ''
                        data['scopus_doi_status'] = "Scopus API failed"

                    if mag_paper_id:
                        tlogger.info("MAG cites: %s" % mag_citations)
                        data['citation_lookup_status'] = "ID in Scopus"
                        data['scopus_doi_status'] = "DOI in Scopus"
                        data['scopus_id'] = mag_paper_id
                        data['citations'] = mag_citations
                    else:
                        tlogger.info("No MAG PaperId found for DOI: %s" % data['xref_doi'])
                        data['scopus_doi_status'] = "No DOI in Scopus"
                        data['citation_lookup_status'] = "No ID in Scopus"
                        data['scopus_id'] = ''

                tlogger.info("Manuscript %s status: %s" % (manuscript_id, data['status']))

                row = '\t'.join([publisher_id, manuscript_id, json.dumps(data)]) + '\n'

                target_file.write(row)

        self.run_pipeline_threads(process_manuscript_rows, manuscript_rows, tlogger=tlogger)

        target_file.close()

        task_args['count'] = count
        task_args['input_file'] = target_file_name
        return task_args
