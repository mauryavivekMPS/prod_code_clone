import csv
import datetime
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import PublishedArticle, PublishedArticleValues


@app.task
class ResolvePublishedArticlesData(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        file = task_args['input_file']
        total_count = task_args['count']

        now = datetime.datetime.now()

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        with open(file, encoding='utf-8') as tsv:
            count = 0
            for line in csv.reader(tsv, delimiter='\t'):

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                # skip header row
                if count == 1:
                    continue

                doi = line[1]
                tlogger.info("Processing #%s : %s" % (count - 1, doi))

                # grab the canonical article record that we're operating on
                try:
                    article = PublishedArticle.objects.get(publisher_id=publisher_id, article_doi=doi)
                except PublishedArticle.DoesNotExist:
                    tlogger.info("DOI does not exist in published_article table")
                    continue

                # resolve policy: if a value from source=custom is present it always wins
                for field in ['article_type', 'subject_category', 'editor', 'custom', 'custom_2', 'custom_3']:
                    new_value = None
                    try:
                        v = PublishedArticleValues.objects.get(article_doi=doi, publisher_id=publisher_id, source='custom', name=field)
                        new_value = v.value_text
                    except PublishedArticleValues.DoesNotExist:
                        pass

                    if not new_value:
                        try:
                            v = PublishedArticleValues.objects.get(article_doi=doi, publisher_id=publisher_id, source='pa', name=field)
                            new_value = v.value_text
                        except PublishedArticleValues.DoesNotExist:
                            pass

                    # update the canonical if there is any non Null/None value (note that "None" is a value)
                    if new_value:
                        setattr(article, field, new_value)

                article.updated = now
                article.save()

        if pipeline_id == 'custom_article_data':
            self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, send_notification_email=True, notification_count=count)

        task_args['count'] = count
        return task_args
