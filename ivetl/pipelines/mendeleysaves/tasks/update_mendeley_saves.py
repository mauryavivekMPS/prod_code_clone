import codecs
import csv
import datetime
import os
import threading

from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from ivetl.celery import app
from ivetl.common import common
from ivetl.connectors import MendeleyConnector
from ivetl.models import PublishedArticle
from ivetl.pipelines.task import Task


@app.task
class UpdateMendeleySaves(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        cluster = Cluster(common.CASSANDRA_IP_LIST)
        session = cluster.connect()

        product = common.PRODUCT_BY_ID[product_id]

        target_file_name = os.path.join(work_folder, "%s_mendeley_target.tab" % publisher_id)

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
                        doi = common.normalizedDoi(line[1])
                        already_processed.add(doi)

        if already_processed:
            tlogger.info('Found %s existing items to reuse' % len(already_processed))
        else:
            tlogger.info('Found no existing items, processing entire article set')

        target_file = codecs.open(target_file_name, 'a', 'utf-16')

        if not already_processed:
            target_file.write('\t'.join(['PUBLISHER_ID', 'DOI', 'SAVES']) + '\n')

        mendeley = MendeleyConnector(common.MENDELEY_CLIENT_ID, common.MENDELEY_CLIENT_SECRET)

        all_articles_sql = """
          select article_doi, mendeley_saves, is_cohort
          from impactvizor.published_article
          where publisher_id = %s
          limit 5000000
        """

        all_articles_statement = SimpleStatement(all_articles_sql, fetch_size=1000)

        # grab all articles and filter manually for cohort
        all_articles = []
        for a in session.execute(all_articles_statement, (publisher_id,)):
            if a.is_cohort == product['cohort'] and a.article_doi not in already_processed:
                all_articles.append(a)

        count = 0
        count_lock = threading.Lock()

        total_count = len(all_articles)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        tlogger.info('Total articles to be processed: %s' % total_count)

        updated_date = datetime.datetime.today()

        def process_article_rows(articles_for_this_thread):
            nonlocal count

            thread_article_count = 0

            for article in articles_for_this_thread:
                with count_lock:
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                thread_article_count += 1

                doi = article.article_doi
                tlogger.info("Retrieving Mendeley for: %s" % doi)

                new_saves_value = None
                try:
                    new_saves_value = mendeley.get_saves(doi)
                except:
                    tlogger.info("General Exception - Mendeley API failed for %s. Skipping" % doi)

                if new_saves_value and article.mendeley_saves != new_saves_value:
                    PublishedArticle.objects(
                        publisher_id=publisher_id,
                        article_doi=doi,
                    ).update(
                        mendeley_saves=new_saves_value,
                        updated=updated_date,
                    )

                row = '\t'.join([publisher_id, doi, str(new_saves_value)]) + '\n'
                target_file.write(row)

        self.run_pipeline_threads(process_article_rows, all_articles, tlogger=tlogger)

        target_file.close()

        task_args['input_file'] = target_file_name
        task_args['count'] = count

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, tlogger, show_alerts=task_args['show_alerts'])

        return task_args
