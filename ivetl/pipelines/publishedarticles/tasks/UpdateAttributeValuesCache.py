import json
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import PublishedArticle, Attribute_Values
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

        total_count = len(all_articles) * len(value_names)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0

        for name in value_names:
            values = set()
            for article in all_articles:
                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                if article[name]:
                    values.add(article[name])

            Attribute_Values.objects(
                publisher_id=publisher_id,
                name='published_article.' + name,
            ).update(
                values_json=json.dumps(list(values))
            )

        if pipeline_id == 'custom_article_data':
            self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, send_notification_email=True, notification_count=count)

        # leave existing task args in place, input_file and count, in particular

        return task_args
