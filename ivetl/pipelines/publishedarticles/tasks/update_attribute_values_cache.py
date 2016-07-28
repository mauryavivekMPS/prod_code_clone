import json
from collections import defaultdict
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import PublishedArticle, AttributeValues
from ivetl.alerts import CHECKS


@app.task
class UpdateAttributeValuesCacheTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        all_articles = PublishedArticle.objects.filter(publisher_id=publisher_id)

        value_names = set()

        # look through all the alerts for published_article values
        for check_id, check in CHECKS.items():
            for f in check.get('filters', []):
                if f['table'] == 'published_article':
                    value_names.add(f['name'])

        total_count = len(all_articles) * (len(value_names) + 1)  # plus one for the special-case citable sections
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0

        for name in value_names:
            values = set()
            for article in all_articles:
                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                if article[name]:
                    values.add(article[name])

            AttributeValues.objects(
                publisher_id=publisher_id,
                name='published_article.' + name,
            ).update(
                values_json=json.dumps(list(values))
            )

        # special publisher-centric caching for citable sections
        values_by_issn = defaultdict(set)
        for article in all_articles:
            if article.article_type and not article.is_cohort:
                values_by_issn[article.article_journal_issn].add(article.article_type)

        for issn, values in values_by_issn.items():
            AttributeValues.objects(
                publisher_id=publisher_id,
                name='citable_sections.' + issn,
            ).update(
                values_json=json.dumps(list(values))
            )

        if pipeline_id == 'custom_article_data':
            self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, send_notification_email=True, notification_count=count)

        # leave existing task args in place, input_file and count, in particular

        return task_args
