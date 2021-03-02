import json
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from collections import defaultdict
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.pipelines.publishedarticles import UpdatePublishedArticlesPipeline
from ivetl.models import AttributeValues
from ivetl.alerts import CHECKS
from ivetl.common import common
from ivetl import utils


@app.task
class UpdateAttributeValuesCacheTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        cluster = Cluster(common.CASSANDRA_IP_LIST)
        session = cluster.connect()

        product = common.PRODUCT_BY_ID[product_id]

        value_names = set()

        # look through all the alerts for published_article values
        for check_id, check in CHECKS.items():
            for f in check.get('filters', []):
                if f['table'] == 'published_article':
                    value_names.add(f['name'])

        value_name_list = ','.join(value_names.union({'article_type', 'article_journal_issn'}))

        all_articles_sql = "select " + value_name_list + """
          from impactvizor.published_article
          where publisher_id = %s
          limit 1000000
        """

        all_articles_statement = SimpleStatement(all_articles_sql, fetch_size=1000)

        all_articles = []
        for a in session.execute(all_articles_statement, (publisher_id,)):
            all_articles.append(a)

        total_count = utils.get_record_count_estimate(publisher_id, product_id, pipeline_id, self.short_name)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0

        for name in value_names:
            values = set()
            for article in all_articles:
                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                value = getattr(article, name)
                if value:
                    values.add(value)

            AttributeValues.objects(
                publisher_id=publisher_id,
                name='published_article.' + name,
            ).update(
                values_json=json.dumps(list(values))
            )

        # special publisher-centric caching for citable sections
        if not product['cohort']:

            electronic_issn_lookup = UpdatePublishedArticlesPipeline.generate_electronic_issn_lookup(publisher_id, product_id)

            # group all of the article_type values for each ISSN by journal (via electronic ISSN)
            values_by_electronic_issn = defaultdict(set)
            for article in all_articles:
                if article.article_type:
                    electronic_issn = electronic_issn_lookup.get(article.article_journal_issn)
                    if electronic_issn:
                        values_by_electronic_issn[electronic_issn].add(article.article_type)

            # add a values record per journal
            for electronic_issn, values in values_by_electronic_issn.items():
                AttributeValues.objects(
                    publisher_id=publisher_id,
                    name='citable_sections.' + electronic_issn,
                ).update(
                    values_json=json.dumps(list(values))
                )

        if pipeline_id in ('custom_article_data',
        'refresh_value_mappings', 'benchpress_published_article_data'):
            self.pipeline_ended(
                publisher_id,
                product_id,
                pipeline_id,
                job_id,
                tlogger,
                task_args=task_args,
                send_notification_email=True,
                force_notification_email=True,
                show_alerts=task_args['show_alerts']
            )

        # leave existing task args in place, input_file and count, in particular

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, count)

        return task_args
