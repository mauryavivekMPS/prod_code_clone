import csv
import datetime

from ivetl.common import common
from ivetl.celery import app
from ivetl.models import PublishedArticle, ArticleUsage
from ivetl.pipelines.task import Task


@app.task
class ResolveArticleUsageData(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        file = task_args['input_file']
        total_count = task_args['count']

        now = datetime.datetime.now()

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0

        with open(file, encoding='utf-8') as tsv:
            for line in csv.reader(tsv, delimiter='\t'):

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                # skip header row
                if count == 1:
                    continue

                doi = common.normalizedDoi(line[1])
                tlogger.info("Processing #%s : %s" % (count - 1, doi))

                try:
                    article = PublishedArticle.objects.get(publisher_id=publisher_id, article_doi=doi)
                except PublishedArticle.DoesNotExist:
                    tlogger.info("DOI does not exist in published_article table")
                    continue

                month_usage_03 = 0
                month_usage_06 = 0
                month_usage_09 = 0
                month_usage_12 = 0
                month_usage_24 = 0
                month_usage_36 = 0
                month_usage_48 = 0
                month_usage_60 = 0
                month_usage_full_03 = 0
                month_usage_full_06 = 0
                month_usage_full_09 = 0
                month_usage_full_12 = 0
                month_usage_full_24 = 0
                month_usage_full_36 = 0
                month_usage_full_48 = 0
                month_usage_full_60 = 0
                month_usage_pdf_03 = 0
                month_usage_pdf_06 = 0
                month_usage_pdf_09 = 0
                month_usage_pdf_12 = 0
                month_usage_pdf_24 = 0
                month_usage_pdf_36 = 0
                month_usage_pdf_48 = 0
                month_usage_pdf_60 = 0
                month_usage_abstract_03 = 0
                month_usage_abstract_06 = 0
                month_usage_abstract_09 = 0
                month_usage_abstract_12 = 0
                month_usage_abstract_24 = 0
                month_usage_abstract_36 = 0
                month_usage_abstract_48 = 0
                month_usage_abstract_60 = 0
                usage_start_date = None

                for usage in ArticleUsage.objects.filter(publisher_id=publisher_id, article_doi=doi):

                    if not usage_start_date:
                        usage_start_date = usage.usage_start_date

                    if usage.month_number <= 3:
                        if usage.usage_type == 'full':
                            month_usage_full_03 += usage.month_usage
                            month_usage_03 += usage.month_usage
                        elif usage.usage_type == 'pdf':
                            month_usage_pdf_03 += usage.month_usage
                            month_usage_03 += usage.month_usage
                        elif usage.usage_type == 'abstract':
                            month_usage_abstract_03 += usage.month_usage
                    if usage.month_number <= 6:
                        if usage.usage_type == 'full':
                            month_usage_full_06 += usage.month_usage
                            month_usage_06 += usage.month_usage
                        elif usage.usage_type == 'pdf':
                            month_usage_pdf_06 += usage.month_usage
                            month_usage_06 += usage.month_usage
                        elif usage.usage_type == 'abstract':
                            month_usage_abstract_06 += usage.month_usage
                    if usage.month_number <= 9:
                        if usage.usage_type == 'full':
                            month_usage_full_09 += usage.month_usage
                            month_usage_09 += usage.month_usage
                        elif usage.usage_type == 'pdf':
                            month_usage_pdf_09 += usage.month_usage
                            month_usage_09 += usage.month_usage
                        elif usage.usage_type == 'abstract':
                            month_usage_abstract_09 += usage.month_usage
                    if usage.month_number <= 12:
                        if usage.usage_type == 'full':
                            month_usage_full_12 += usage.month_usage
                            month_usage_12 += usage.month_usage
                        elif usage.usage_type == 'pdf':
                            month_usage_pdf_12 += usage.month_usage
                            month_usage_12 += usage.month_usage
                        elif usage.usage_type == 'abstract':
                            month_usage_abstract_12 += usage.month_usage
                    if usage.month_number <= 24:
                        if usage.usage_type == 'full':
                            month_usage_full_24 += usage.month_usage
                            month_usage_24 += usage.month_usage
                        elif usage.usage_type == 'pdf':
                            month_usage_pdf_24 += usage.month_usage
                            month_usage_24 += usage.month_usage
                        elif usage.usage_type == 'abstract':
                            month_usage_abstract_24 += usage.month_usage
                    if usage.month_number <= 36:
                        if usage.usage_type == 'full':
                            month_usage_full_36 += usage.month_usage
                            month_usage_36 += usage.month_usage
                        elif usage.usage_type == 'pdf':
                            month_usage_pdf_36 += usage.month_usage
                            month_usage_36 += usage.month_usage
                        elif usage.usage_type == 'abstract':
                            month_usage_abstract_36 += usage.month_usage
                    if usage.month_number <= 48:
                        if usage.usage_type == 'full':
                            month_usage_full_48 += usage.month_usage
                            month_usage_48 += usage.month_usage
                        elif usage.usage_type == 'pdf':
                            month_usage_pdf_48 += usage.month_usage
                            month_usage_48 += usage.month_usage
                        elif usage.usage_type == 'abstract':
                            month_usage_abstract_48 += usage.month_usage
                    if usage.month_number <= 60:
                        if usage.usage_type == 'full':
                            month_usage_full_60 += usage.month_usage
                            month_usage_60 += usage.month_usage
                        elif usage.usage_type == 'pdf':
                            month_usage_pdf_60 += usage.month_usage
                            month_usage_60 += usage.month_usage
                        elif usage.usage_type == 'abstract':
                            month_usage_abstract_60 += usage.month_usage

                article.month_usage_03 = month_usage_03
                article.month_usage_06 = month_usage_06
                article.month_usage_09 = month_usage_09
                article.month_usage_12 = month_usage_12
                article.month_usage_24 = month_usage_24
                article.month_usage_36 = month_usage_36
                article.month_usage_48 = month_usage_48
                article.month_usage_60 = month_usage_60
                article.month_usage_full_03 = month_usage_full_03
                article.month_usage_full_06 = month_usage_full_06
                article.month_usage_full_09 = month_usage_full_09
                article.month_usage_full_12 = month_usage_full_12
                article.month_usage_full_24 = month_usage_full_24
                article.month_usage_full_36 = month_usage_full_36
                article.month_usage_full_48 = month_usage_full_48
                article.month_usage_full_60 = month_usage_full_60
                article.month_usage_pdf_03 = month_usage_pdf_03
                article.month_usage_pdf_06 = month_usage_pdf_06
                article.month_usage_pdf_09 = month_usage_pdf_09
                article.month_usage_pdf_12 = month_usage_pdf_12
                article.month_usage_pdf_24 = month_usage_pdf_24
                article.month_usage_pdf_36 = month_usage_pdf_36
                article.month_usage_pdf_48 = month_usage_pdf_48
                article.month_usage_pdf_60 = month_usage_pdf_60
                article.month_usage_abstract_03 = month_usage_abstract_03
                article.month_usage_abstract_06 = month_usage_abstract_06
                article.month_usage_abstract_09 = month_usage_abstract_09
                article.month_usage_abstract_12 = month_usage_abstract_12
                article.month_usage_abstract_24 = month_usage_abstract_24
                article.month_usage_abstract_36 = month_usage_abstract_36
                article.month_usage_abstract_48 = month_usage_abstract_48
                article.month_usage_abstract_60 = month_usage_abstract_60

                article.usage_start_date = usage_start_date
                article.updated = now
                article.save()

            tsv.close()

        if pipeline_id == 'article_usage':
            self.pipeline_ended(
                publisher_id,
                product_id,
                pipeline_id,
                job_id,
                tlogger,
                task_args=task_args,
                send_notification_email=True,
                show_alerts=task_args['show_alerts']
            )

        task_args['count'] = count
        return task_args
