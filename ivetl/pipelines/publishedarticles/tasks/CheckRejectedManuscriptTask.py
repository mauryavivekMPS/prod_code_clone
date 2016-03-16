from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import Published_Article, Rejected_Articles, Pipeline_Status
from ivetl.pipelines.articlecitations import UpdateArticleCitationsPipeline


@app.task
class CheckRejectedManuscriptTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        total_count = task_args['count']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

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
            count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, len(articles), count)

            tlogger.info("---")
            tlogger.info("%s of %s. Looking Up rejected manuscript for %s / %s" % (count, len(articles), publisher_id, article.article_doi))

            rm = rm_map.get(article.article_doi)
            if rm:
                article.from_rejected_manuscript = True
                article.rejected_manuscript_id = rm.manuscript_id
                article.rejected_manuscript_editor = rm.editor
                article.date_of_rejection = rm.date_of_rejection
                article.update()
                tlogger.info("Article sourced from rejected manuscript.")

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, send_notification_email=True, notification_count=total_count)

        if pipeline_id in ("published_articles", "cohort_articles") and task_args['run_monthly_job']:
            pipeline_status = Pipeline_Status.objects.get(
                publisher_id=publisher_id,
                product_id=product_id,
                pipeline_id=pipeline_id,
                job_id=job_id,
            )

            UpdateArticleCitationsPipeline.s(
                publisher_id_list=[publisher_id],
                product_id=product_id,
                initiating_user_email=pipeline_status.user_email,
                job_id=job_id,
            ).delay()

        return {'count': count}
