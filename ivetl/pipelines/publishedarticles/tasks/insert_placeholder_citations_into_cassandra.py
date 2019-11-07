from datetime import datetime

from ivetl.common import common
from ivetl.celery import app
from ivetl.models import PublishedArticle, ArticleCitations
from ivetl.pipelines.task import Task


@app.task
class InsertPlaceholderCitationsIntoCassandraTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        article_limit = 1000000

        articles = PublishedArticle.objects.filter(publisher_id=publisher_id).fetch_size(1000).limit(article_limit)
        count = 0
        total_count = len(articles)
        today = datetime.today()
        updated = today

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        for article in articles:
            count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
            tlogger.info("---")
            tlogger.info("%s of %s. Adding placeholder citations for %s / %s" % (count, len(articles), publisher_id, article.article_doi))

            for yr in range(article.date_of_publication.year, today.year + 1):
                plac = ArticleCitations()
                plac['publisher_id'] = publisher_id
                plac['article_doi'] = common.normalizedDoi(article.article_doi)
                plac['citation_doi'] = str(yr) + "-placeholder"
                plac['updated'] = updated
                plac['created'] = updated
                plac['citation_date'] = datetime(yr, 1, 1)
                plac['citation_count'] = 0
                plac['is_cohort'] = article.is_cohort
                plac['citation_source_xref'] = True
                plac['citation_source_scopus'] = True
                plac.save()

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, tlogger, show_alerts=task_args['show_alerts'])

        task_args['count'] = count
        return task_args


def to_date_time(month, day, year):

    if year < 99:
        year += 2000

    # date (y, m, d)
    date = datetime(year, month, day)
    return date








