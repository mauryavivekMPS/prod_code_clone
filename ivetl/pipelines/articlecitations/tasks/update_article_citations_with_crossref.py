import codecs
import csv
import datetime
import os
import threading

from ivetl.celery import app
from ivetl.common import common
from ivetl.connectors import CrossrefConnector, MaxTriesAPIError
from ivetl.models import PublisherMetadata, PublishedArticleByCohort, ArticleCitations, PublishedArticle
from ivetl.pipelines.task import Task


@app.task
class UpdateArticleCitationsWithCrossref(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        total_count = task_args['count']

        publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)

        if not publisher.supports_crossref:
            tlogger.info("Publisher is not configured for crossref")
            self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, tlogger, show_alerts=task_args['show_alerts'])
            return {'count': 0}

        product = common.PRODUCT_BY_ID[product_id]
        if product['cohort']:
            tlogger.info("Cohort product does not support crossref")
            self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, tlogger, show_alerts=task_args['show_alerts'])
            return {'count': 0}

        target_file_name = work_folder + "/" + publisher_id + "_" + "updatearticles" + "_" + "target.tab"

        def reader_without_unicode_breaks(f):
            while True:
                yield next(f).replace('\ufeff', '')
                continue

        already_processed = set()

        # if the file exists, read it in assuming a job restart
        if os.path.isfile(target_file_name):
            with codecs.open(target_file_name, encoding='utf-16') as tsv:
                for line in csv.reader(reader_without_unicode_breaks(tsv), delimiter='\t'):
                    if line and len(line) == 2 and line[0] != 'PUBLISHER_ID':
                        doi = common.normalizedDoi(line[1])
                        already_processed.add(doi)

        if already_processed:
            tlogger.info('Found %s existing items to reuse' % len(already_processed))

        target_file = codecs.open(target_file_name, 'a', 'utf-16')
        if not already_processed:
            target_file.write('\t'.join(['PUBLISHER_ID', 'DOI']) + '\n')

        count = 0
        count_lock = threading.Lock()

        all_articles = []

        for article in PublishedArticleByCohort.objects.filter(publisher_id=publisher_id, is_cohort=False).fetch_size(1000).limit(50000000):
            if article.article_doi in already_processed:
                continue
            all_articles.append(article)

        total_count = len(all_articles)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        tlogger.info('Total articles to be processed: %s' % total_count)

        crossref = CrossrefConnector(publisher.crossref_username, publisher.crossref_password, tlogger)
        updated_date = datetime.datetime.today()

        def process_articles(articles_for_this_thread):
            nonlocal count

            thread_article_count = 0

            for article in articles_for_this_thread:
                with count_lock:
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                thread_article_count += 1

                doi = common.normalizedDoi(article.article_doi)

                tlogger.info("Looking up citations for %s" % doi)

                try:
                    citations = crossref.get_citations(doi)

                    process_this_article = True

                    num_citations = len(citations)
                    if article.crossref_citation_count == num_citations:
                        # assume they are all the same and skip everything below
                        tlogger.info('Number of citations unchanged for %s , skipping' % doi)
                        process_this_article = False
                    else:
                        article.crossref_citation_count = num_citations
                        article.save()

                    if process_this_article:
                        for citation_doi in citations:
                            add_citation = False

                            citation_doi = common.normalizeDoi(citation_doi)

                            try:
                                existing_citation = ArticleCitations.objects.get(
                                    publisher_id=publisher_id,
                                    article_doi=doi,
                                    citation_doi=citation_doi
                                )

                                if existing_citation.citation_source_xref is not True:
                                    tlogger.info("Found existing Scopus citation %s in crossref" % citation_doi)
                                    existing_citation.citation_source_xref = True
                                    existing_citation.save()

                            except ArticleCitations.DoesNotExist:
                                tlogger.info("Found new citation %s in crossref, adding record" % citation_doi)
                                add_citation = True

                            if add_citation:
                                data = crossref.get_article(citation_doi)

                                if data:

                                    if data['date'] is None:
                                        tlogger.info("No citation date available for citation %s, skipping" % citation_doi)
                                        continue

                                    ArticleCitations.create(
                                        publisher_id=publisher_id,
                                        article_doi=doi,
                                        citation_doi=common.normalizedDoi(data['doi']),
                                        citation_scopus_id=data.get('scopus_id', None),
                                        citation_date=data['date'],
                                        citation_first_author=data['first_author'],
                                        citation_issue=data['issue'],
                                        citation_journal_issn=data['journal_issn'],
                                        citation_journal_title=data['journal_title'],
                                        citation_pages=data['pages'],
                                        citation_source_xref=True,
                                        citation_title=data['title'],
                                        citation_volume=data['volume'],
                                        citation_count=1,
                                        updated=updated_date,
                                        created=updated_date,
                                    )
                                else:
                                    tlogger.info("No crossref data found for citation %s, skipping" % citation_doi)

                except MaxTriesAPIError:
                    tlogger.info("Crossref API failed for %s" % doi)

                published_article = PublishedArticle.objects.get(publisher_id=publisher_id, article_doi=doi)
                old_citation_count = published_article.citation_count
                new_citation_count = ArticleCitations.objects.filter(publisher_id=publisher_id, article_doi=doi).fetch_size(1000).limit(50000000).count()

                published_article.update(
                    previous_citation_count=old_citation_count,
                    citation_count=new_citation_count
                )

                row = '\t'.join([publisher_id, doi]) + '\n'

                target_file.write(row)

        self.run_pipeline_threads(process_articles, all_articles, tlogger=tlogger)

        target_file.close()

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, tlogger, show_alerts=task_args['show_alerts'])

        task_args['count'] = count
        return task_args
