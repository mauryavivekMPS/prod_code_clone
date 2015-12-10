import csv
import datetime
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import Published_Article, Article_Usage


@app.task
class ResolveArticleUsageData(Task):

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

                try:
                    article = Published_Article.objects.get(publisher_id=publisher_id, article_doi=doi)
                except Published_Article.DoesNotExist:
                    tlogger.info("DOI does not exist in published_article table")
                    continue

                month_usage_03 = 0
                month_usage_06 = 0
                month_usage_09 = 0
                month_usage_12 = 0
                month_usage_24 = 0
                month_usage_36 = 0
                usage_start_date = None

                for usage in Article_Usage.objects.filter(publisher_id=publisher_id, article_doi=doi):

                    if not usage_start_date:
                        usage_start_date = usage.usage_start_date

                    if usage.month_number <= 3:
                        month_usage_03 += usage.month_usage
                    elif usage.month_number <= 6:
                        month_usage_06 += usage.month_usage
                    elif usage.month_number <= 9:
                        month_usage_09 += usage.month_usage
                    elif usage.month_number <= 12:
                        month_usage_12 += usage.month_usage
                    elif usage.month_number <= 24:
                        month_usage_24 += usage.month_usage
                    elif usage.month_number <= 36:
                        month_usage_36 += usage.month_usage

                article.month_usage_03 = month_usage_03
                article.month_usage_06 = month_usage_06
                article.month_usage_09 = month_usage_09
                article.month_usage_12 = month_usage_12
                article.month_usage_24 = month_usage_24
                article.month_usage_36 = month_usage_36
                article.usage_start_date = usage_start_date
                article.updated = now
                article.save()

            tsv.close()

        if pipeline_id == 'article_usage':
            self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, send_notification_email=True, notification_count=count)

        task_args['count'] = count
        return task_args
