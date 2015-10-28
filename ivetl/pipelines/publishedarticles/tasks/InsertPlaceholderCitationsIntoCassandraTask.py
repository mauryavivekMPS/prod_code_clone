import os
import csv
import codecs
import json
from datetime import datetime
from ivetl.celery import app
from ivetl.common.BaseTask import BaseTask
from ivetl.models import Published_Article, Publisher_Vizor_Updates, Publisher_Metadata, Article_Citations, Published_Article_Values, Issn_Journal
from ivetl.pipelines.task import Task


@app.task
class InsertPlaceholderCitationsIntoCassandraTask(Task):

    def run_task(self, publisher_id, job_id, work_folder, tlogger, task_args):

        article_limit = 1000000

        articles = Published_Article.objects.filter(publisher_id=publisher_id).limit(article_limit)
        count = 0
        today = datetime.today()
        updated = today

        for article in articles:
            count += 1
            tlogger.info("---")
            tlogger.info("%s of %s. Adding placeholder citations for %s / %s" % (count, len(articles), publisher_id, article.article_doi))

            for yr in range(article.date_of_publication.year, today.year + 1):
                plac = Article_Citations()
                plac['publisher_id'] = publisher_id
                plac['article_doi'] = article.article_doi
                plac['citation_doi'] = str(yr) + "-placeholder"
                plac['updated'] = updated
                plac['created'] = updated
                plac['citation_date'] = datetime(yr, 1, 1)
                plac['citation_count'] = 0
                plac.save()

        self.pipeline_ended(publisher_id, job_id)
        return {self.COUNT: count}


def to_date_time(month, day, year):

    if year < 99:
        year += 2000

    # date (y, m, d)
    date = datetime(year, month, day)
    return date








