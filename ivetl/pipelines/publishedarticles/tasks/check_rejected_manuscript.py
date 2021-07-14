import datetime

from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from ivetl.celery import app
from ivetl.common import common
from ivetl import utils
from ivetl.models import PublishedArticle, RejectedArticles, PipelineStatus
from ivetl.pipelines.articlecitations import UpdateArticleCitationsPipeline
from ivetl.pipelines.task import Task


@app.task
class CheckRejectedManuscriptTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        cluster = Cluster(common.CASSANDRA_IP_LIST)
        session = cluster.connect()

        total_count = utils.get_record_count_estimate(publisher_id, product_id, pipeline_id, self.short_name)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        rejected_articles_sql = """
          select crossref_doi, manuscript_id, editor, date_of_rejection, status
          from impactvizor.rejected_articles
          where publisher_id = %s
          limit 1000000
        """

        rejected_articles_statement = SimpleStatement(rejected_articles_sql, fetch_size=1000)

        rm_map = {}
        for rejected_article_row in session.execute(rejected_articles_statement, (publisher_id,)):
            if rejected_article_row.status != 'Not Published':
                rm_map[rejected_article_row.crossref_doi] = (
                    rejected_article_row.manuscript_id,
                    rejected_article_row.editor,
                    rejected_article_row.date_of_rejection
                )

        article_limit = 1000000
        if 'max_articles_to_process' in task_args and task_args['max_articles_to_process']:
            article_limit = task_args['max_articles_to_process']

        all_articles_sql = """
          select article_doi, from_rejected_manuscript, rejected_manuscript_id, rejected_manuscript_editor, date_of_rejection
          from impactvizor.published_article
          where publisher_id = %s
          limit %s
        """

        all_articles_statement = SimpleStatement(all_articles_sql, fetch_size=1000)

        count = 0
        for article_row in session.execute(all_articles_statement, (publisher_id, article_limit)):

            count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

            tlogger.info("%s of %s. Looking up rejected manuscript for %s / %s (est)" % (count, total_count, publisher_id, article_row.article_doi))

            rm = rm_map.get(article_row.article_doi)
            if rm:
                manuscript_id, editor, date_of_rejection = rm
                PublishedArticle.objects(
                    publisher_id=publisher_id,
                    article_doi=common.normalizedDoi(article_row.article_doi),
                ).update(
                    from_rejected_manuscript=True,
                    rejected_manuscript_id=manuscript_id,
                    rejected_manuscript_editor=editor,
                    date_of_rejection=date_of_rejection,
                )
                tlogger.info("Article sourced from rejected manuscript")
            elif article_row.from_rejected_manuscript:
                # published_article row was previously matched,
                # however rejected manuscript is now matched to another article
                # cleanup / reset previous rejected article match data
                PublishedArticle.objects(
                  publisher_id=publisher_id,
                  article_doi=common.normalizedDoi(article_row.article_doi),
                ).update(
                    from_rejected_manuscript=False,
                    rejected_manuscript_id=None,
                    rejected_manuscript_editor=None,
                    date_of_rejection=None,
                )
                tlogger.info("Article previously matched to rejected manuscript, but no longer does.")
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
