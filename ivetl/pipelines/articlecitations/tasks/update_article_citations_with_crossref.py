import datetime
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.common import common
from ivetl.connectors import CrossrefConnector, MaxTriesAPIError
from ivetl.models import PublisherMetadata, PublishedArticleByCohort, ArticleCitations, PublishedArticle
from ivetl.alerts import run_alerts, send_alert_notifications


@app.task
class UpdateArticleCitationsWithCrossref(Task):
    PUBLISHED_ARTICLE_QUERY_LIMIT = 50000000
    ARTICLE_CITATION_QUERY_LIMIT = 50000000

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        total_count = task_args['count']

        publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)

        count = 0
        error_count = 0

        if not publisher.supports_crossref:
            tlogger.info("Publisher is not configured for crossref")
            self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, tlogger)
            return {'count': count}

        product = common.PRODUCT_BY_ID[product_id]
        if product['cohort']:
            tlogger.info("Cohort product does not support crossref")
            self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, tlogger)
            return {'count': count}

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        crossref = CrossrefConnector(publisher.crossref_username, publisher.crossref_password, tlogger)
        articles = PublishedArticleByCohort.objects.filter(publisher_id=publisher_id, is_cohort=False).fetch_size(1000).limit(self.PUBLISHED_ARTICLE_QUERY_LIMIT)
        updated_date = datetime.datetime.today()

        for article in articles:
            count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

            doi = article.article_doi

            tlogger.info("---")
            tlogger.info("%s of %s. Looking Up citations for %s / %s" % (count, len(articles), publisher_id, doi))

            citations = []

            try:
                citations = crossref.get_citations(doi)
            except MaxTriesAPIError:
                tlogger.info("Crossref API failed for %s" % doi)
                error_count += 1

            for citation_doi in citations:

                add_citation = False

                try:
                    existing_citation = ArticleCitations.objects.get(
                        publisher_id=publisher_id,
                        article_doi=doi,
                        citation_doi=citation_doi
                    )

                    if existing_citation.citation_source_scopus is not True and existing_citation.citation_source_xref is True:
                        add_citation = True

                    else:
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
                            citation_doi=data['doi'],
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

            published_article = PublishedArticle.objects.get(publisher_id=publisher_id, article_doi=doi)
            old_citation_count = published_article.citation_count
            new_citation_count = ArticleCitations.objects.filter(publisher_id=publisher_id, article_doi=doi).fetch_size(1000).limit(self.ARTICLE_CITATION_QUERY_LIMIT).count()
            issn = published_article.article_journal_issn

            # Just for testing!!
            # new_citation_count += int(old_citation_count * 1.4)

            run_alerts(
                check_ids=['citations-exceeds-integer', 'citations-percentage-change'],
                publisher_id=publisher_id,
                product_id=product_id,
                pipeline_id=pipeline_id,
                job_id=job_id,
                old_value=old_citation_count,
                new_value=new_citation_count,
                extra_values={
                    'doi': doi,
                    'issn': issn,
                    'article_type': published_article.article_type,
                    'subject_category': published_article.subject_category,
                    'custom': published_article.custom,
                    'custom_2': published_article.custom_2,
                    'custom_3': published_article.custom_3,
                    'article_title': published_article.article_title,
                }
            )

            # update the count *after* we've compared the new to old
            published_article.update(
                previous_citation_count=old_citation_count,
                citation_count=new_citation_count
            )

        send_alert_notifications(
            check_ids=['citations-exceeds-integer', 'citations-percentage-change'],
            publisher_id=publisher_id,
            product_id=product_id,
            pipeline_id=pipeline_id,
            job_id=job_id,
        )

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, tlogger)

        return {
            'count': count
        }
