__author__ = 'nmehta'

from time import time
from datetime import datetime
from os import makedirs
from ivetl.common import common
from ivetl.celery import app
from ivetl.models.PublishedArticle import Published_Article
from ivetl.models.ArticleCitations import Article_Citations
from ivetl.pipelines.task import Task


@app.task
class InsertArticleCitationPlaceholderTask(Task):
    taskname = "InsertArticleCitationPlaceholder"
    vizor = common.AC

    QUERY_LIMIT = 500000

    def run(self, publisher):

        today = datetime.today()
        updated = today

        workfolder = common.BASE_WORK_DIR + today.strftime('%Y%m%d') + "/" + publisher + "/" + self.vizor + "/" + today.strftime('%Y%m%d') + "_" + today.strftime('%H%M%S%f')

        path = workfolder + "/" + self.taskname
        makedirs(path, exist_ok=True)

        tlogger = self.getTaskLogger(path, self.taskname)

        t0 = time()
        count = 0

        articles = Published_Article.objects.filter(publisher_id=publisher).limit(self.QUERY_LIMIT)

        for article in articles:

            count += 1

            # Add placeholder record for each year of citation
            for yr in range(article.date_of_publication.year, today.year + 1):

                    plac = Article_Citations()
                    plac['publisher_id'] = publisher
                    plac['article_doi'] = article.article_doi
                    plac['citation_doi'] = str(yr) + "-placeholder"
                    plac['updated'] = updated
                    plac['created'] = updated
                    plac['citation_date'] = datetime(yr, 1, 1)
                    plac['citation_count'] = 0
                    plac.save()

            tlogger.info("---")
            tlogger.info(str(count-1) + ". " + publisher + " / " + article.article_doi + ": Inserted placeholder citations.")

        t1 = time()
        tlogger.info("Time Taken:       " + format(t1-t0, '.2f') + " seconds / " + format((t1-t0)/60, '.2f') + " minutes")

        return