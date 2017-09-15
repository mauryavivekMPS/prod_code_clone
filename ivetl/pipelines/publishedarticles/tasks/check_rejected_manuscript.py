import datetime
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import PublishedArticle, RejectedArticles, PipelineStatus
from ivetl.pipelines.articlecitations import UpdateArticleCitationsPipeline
from ivetl import utils


@app.task
class CheckRejectedManuscriptTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        total_count = utils.get_record_count_estimate(publisher_id, product_id, pipeline_id, self.short_name)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        article_limit = 1000000
        if 'max_articles_to_process' in task_args and task_args['max_articles_to_process']:
            article_limit = task_args['max_articles_to_process']

        articles = PublishedArticle.objects.filter(publisher_id=publisher_id).fetch_size(1000).limit(article_limit)
        rm_map = {}

        rms = RejectedArticles.objects.filter(publisher_id=publisher_id).fetch_size(1000).limit(1000000)
        for r in rms:
            if r.status != 'Not Published':
                rm_map[r.crossref_doi] = (r.manuscript_id, r.editor, r.date_of_rejection)

        count = 0
        for article in articles:
            count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

            tlogger.info("---")
            tlogger.info("%s of %s. Looking Up rejected manuscript for %s / %s (est)" % (count, total_count, publisher_id, article.article_doi))

            rm = rm_map.get(article.article_doi)
            if rm:
                manuscript_id, editor, date_of_rejection = rm
                article.from_rejected_manuscript = True
                article.rejected_manuscript_id = manuscript_id
                article.rejected_manuscript_editor = editor
                article.date_of_rejection = date_of_rejection
                article.update()
                tlogger.info("Article sourced from rejected manuscript.")

        run_monthly_jobs = task_args.get('run_monthly_job', False)

        self.pipeline_ended(
            publisher_id,
            product_id,
            pipeline_id,
            job_id,
            tlogger,
            task_args=task_args,
            send_notification_email=True,
            run_monthly_job=run_monthly_jobs,
            show_alerts=task_args.get('show_alerts', False),
        )

        if pipeline_id in ("published_articles", "cohort_articles"):
            utils.update_high_water(product_id, pipeline_id, publisher_id, datetime.datetime.now())

        if pipeline_id in ("published_articles", "cohort_articles") and run_monthly_jobs:
            pipeline_status = PipelineStatus.objects.get(
                publisher_id=publisher_id,
                product_id=product_id,
                pipeline_id=pipeline_id,
                job_id=job_id,
            )

            citation_product_id = None
            if product_id == 'published_articles':
                citation_product_id = 'article_citations'
            elif product_id == 'cohort_articles':
                citation_product_id = 'cohort_citations'

            if citation_product_id:
                UpdateArticleCitationsPipeline.s(
                    publisher_id_list=[publisher_id],
                    product_id=citation_product_id,
                    initiating_user_email=pipeline_status.user_email,
                    job_id=job_id,
                ).delay()

        # true up the count
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, count)

        task_args['count'] = count
        return task_args
