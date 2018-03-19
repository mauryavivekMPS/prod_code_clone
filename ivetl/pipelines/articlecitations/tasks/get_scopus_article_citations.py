import os
import json
import codecs
import csv
import threading
import traceback
from ivetl.celery import app
from ivetl.connectors import ScopusConnector, MaxTriesAPIError
from ivetl.models import PublisherMetadata, PublishedArticleByCohort, ArticleCitations
from ivetl.pipelines.task import Task
from ivetl.common import common


@app.task
class GetScopusArticleCitations(Task):
    QUERY_LIMIT = 50000000
    MAX_ERROR_COUNT = 100

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        product = common.PRODUCT_BY_ID[product_id]

        target_file_name = os.path.join(work_folder, "%s_articlecitations_target.tab" % publisher_id)

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
                        already_processed.add(line[1])

        if already_processed:
            tlogger.info('Found %s existing items to reuse' % len(already_processed))
        else:
            tlogger.info('Found no existing items, processing entire article set')

        target_file = codecs.open(target_file_name, 'a', 'utf-16')

        if not already_processed:
            target_file.write('PUBLISHER_ID\tDOI\tDATA\n')

        pm = PublisherMetadata.objects.get(publisher_id=publisher_id)
        scopus = ScopusConnector(pm.scopus_api_keys)

        if product['cohort']:
            articles = PublishedArticleByCohort.objects.filter(publisher_id=publisher_id, is_cohort=True).fetch_size(1000).limit(self.QUERY_LIMIT)
        else:
            articles = PublishedArticleByCohort.objects.filter(publisher_id=publisher_id, is_cohort=False).fetch_size(1000).limit(self.QUERY_LIMIT)

        count = 0
        stop = False
        count_and_stop_lock = threading.Lock()

        total_count = len(articles)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        tlogger.info('Total article count: %s' % total_count)

        def process_articles(articles_for_this_thread):
            nonlocal count
            nonlocal stop
            error_count = 0

            thread_article_count = 0

            for article in articles_for_this_thread:

                with count_and_stop_lock:
                    if stop:
                        break
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                thread_article_count += 1

                doi = article.article_doi

                tlogger.info('Starting on article %s (%s)' % (doi, article.article_scopus_id))

                if doi in already_processed:
                    continue

                def should_get_citation_details(citation_doi):
                    try:
                        ArticleCitations.objects.get(
                            publisher_id=publisher_id,
                            article_doi=doi,
                            citation_doi=citation_doi
                        )
                        return False
                    except ArticleCitations.DoesNotExist:
                        return True

                if article.article_scopus_id is None or article.article_scopus_id == '':
                    tlogger.info('No scopus ID, skipping %s' % doi)
                    continue

                try:
                    citations, num_citations, skipped = scopus.get_citations(
                        article.article_scopus_id,
                        article.is_cohort,
                        tlogger,
                        should_get_citation_details=should_get_citation_details,
                        existing_count=article.scopus_citation_count
                    )

                    if article.scopus_citation_count != num_citations:
                        article.scopus_citation_count = num_citations
                        article.save()

                    tlogger.info('Total citations found for %s (%s): %s' % (doi, article.article_scopus_id, num_citations))

                    if skipped:
                        tlogger.info('No new/unprocessed citations found for %s (%s), skipping' % (doi, article.article_scopus_id))
                    else:
                        tlogger.info('New citations to be processed for %s (%s): %s' % (doi, article.article_scopus_id, len(citations)))
                        row = "%s\t%s\t%s\n" % (publisher_id, doi, json.dumps(citations))
                        target_file.write(row)

                except MaxTriesAPIError:
                    tlogger.info('Scopus API failed more than MaxTries for %s (%s), skipping' % (doi, article.article_scopus_id))
                    error_count += 1

                except:
                    tlogger.error('Unknown exception in article citation thread:')
                    tlogger.error(traceback.format_exc())
                    with count_and_stop_lock:
                        stop = True
                        break

                if error_count >= self.MAX_ERROR_COUNT:
                    tlogger.info('Scopus API failed more than MaxTries for %s (%s), skipping' % (doi, article.article_scopus_id))
                    raise MaxTriesAPIError(self.MAX_ERROR_COUNT)

        self.run_pipeline_threads(process_articles, articles, tlogger=tlogger)

        target_file.close()

        if stop:
            raise Exception('Stopping job, unexpected error thrown in thread. See logs.')

        task_args['count'] = total_count
        task_args['input_file'] = target_file_name

        return task_args
