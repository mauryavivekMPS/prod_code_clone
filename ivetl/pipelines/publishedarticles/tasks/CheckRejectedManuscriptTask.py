import csv
import datetime
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import Published_Article, Rejected_Articles


@app.task
class CheckRejectedManuscriptTask(Task):

    def run_task(self, publisher_id, job_id, work_folder, tlogger, task_args):

        article_limit = 1000000
        if 'max_articles_to_process' in task_args and task_args['max_articles_to_process']:
            article_limit = task_args['max_articles_to_process']

        articles = Published_Article.objects.filter(publisher_id=publisher_id).limit(article_limit)
        rm_map = {}

        rms = Rejected_Articles.objects.filter(publisher_id=publisher_id).limit(1000000)
        for r in rms:
            if r.status != 'Not Published':
                rm_map[r.crossref_doi] = r

        count = 0
        for article in articles:
            count += 1
            tlogger.info("---")
            tlogger.info("%s of %s. Looking Up rejected manuscript for %s / %s" % (count, len(articles), publisher_id, article.article_doi))

            rm = rm_map[article.article_doi]
            if rm:
                article.from_rejected_manuscript = True
                article.rejected_manuscript_id = rm.manuscript_id
                article.rejected_manuscript_editor = rm.editor
                article.date_of_rejection = rm.date_of_rejection
                article.update()

        self.pipeline_ended(publisher_id, job_id)
        return {self.COUNT: count}
