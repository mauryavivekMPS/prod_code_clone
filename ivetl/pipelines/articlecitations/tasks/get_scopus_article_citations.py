import os
import json
import codecs
import csv
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
                        doi = line[1]
                        already_processed.add(doi)

        if already_processed:
            tlogger.info('Found %s existing items to reuse' % len(already_processed))

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
        error_count = 0

        total_count = len(articles)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        for article in articles:

            count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

            doi = article.article_doi

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
                tlogger.info("Skipping - No Scopus Id")
                continue

            citations = []
            try:
                citations, skipped = scopus.get_citations(
                    article.article_scopus_id,
                    article.is_cohort,
                    tlogger,
                    should_get_citation_details=should_get_citation_details,
                    existing_count=article.scopus_citation_count
                )

                if skipped:
                    tlogger.info('No new citations found, skipping article')
                else:
                    tlogger.info("%s citations retrieved from Scopus" % len(citations))
                    row = "%s\t%s\t%s\n" % (publisher_id, doi, json.dumps(citations))
                    target_file.write(row)

            except MaxTriesAPIError:
                tlogger.info("Scopus API failed for %s" % article.article_scopus_id)
                error_count += 1

            if error_count >= self.MAX_ERROR_COUNT:
                    raise MaxTriesAPIError(self.MAX_ERROR_COUNT)

        target_file.close()

        task_args['count'] = total_count
        task_args['input_file'] = target_file_name

        return task_args
