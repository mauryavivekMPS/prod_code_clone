import datetime
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.connectors import CrossrefConnector, MaxTriesAPIError
from ivetl.models import Publisher_Metadata, Published_Article, Article_Citations


@app.task
class UpdateArticleCitationsWithCrossref(Task):
    QUERY_LIMIT = 500000

    def run_task(self, publisher_id, job_id, work_folder, tlogger, task_args):
        publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)
        crossref = CrossrefConnector(publisher.crossref_username, publisher.crossref_password, tlogger)
        articles = Published_Article.objects.filter(publisher_id=publisher_id).limit(self.QUERY_LIMIT)
        updated_date = datetime.datetime.today()

        count = 0
        error_count = 0

        for article in articles:
            count += 1
            tlogger.info("---")
            tlogger.info("%s of %s. Looking Up citations for %s / %s" % (count, len(articles), publisher_id, article.article_doi))
            citations = []

            try:
                citations = crossref.get_citations(article.article_doi)
            except MaxTriesAPIError:
                tlogger.info("Crossref API failed for %s" % article.article_doi)
                error_count += 1

            for citation_doi in citations:

                add_citation = False

                try:
                    existing_citation = Article_Citations.objects.get(
                        publisher_id=publisher_id,
                        article_doi=article.article_doi,
                        citation_doi=citation_doi
                    )

                    if len(existing_citation.citation_sources) == 1 and 'Crossref' in existing_citation.citation_sources:
                        add_citation = True

                    else:
                        tlogger.info("Found existing citation %s in crossref, appending to sources" % citation_doi)

                        if 'Crossref' not in existing_citation.citation_sources:
                            existing_citation.citation_sources.append('Crossref')
                            existing_citation.save()

                except Article_Citations.DoesNotExist:
                    tlogger.info("Found new citation %s in crossref, adding record" % citation_doi)
                    add_citation = True

                if add_citation:
                    data = crossref.get_article(citation_doi)
                    if data:
                        Article_Citations.create(
                            publisher_id=publisher_id,
                            article_doi=article.article_doi,
                            citation_doi=data['doi'],
                            citation_scopus_id=data.get('scopus_id', None),
                            citation_date=data['date'],
                            citation_first_author=data['first_author'],
                            citation_issue=data['issue'],
                            citation_journal_issn=data['journal_issn'],
                            citation_journal_title=data['journal_title'],
                            citation_pages=data['pages'],
                            citation_sources=[data['source']],
                            citation_title=data['title'],
                            citation_volume=data['volume'],
                            citation_count=1,
                            updated=updated_date,
                            created=updated_date,
                        )
                    else:
                        tlogger.info("No crossref data found for citation %s, skipping" % citation_doi)

        self.pipeline_ended(publisher_id, job_id)

        return {self.COUNT: count}
