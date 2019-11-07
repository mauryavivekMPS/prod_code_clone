import csv
import decimal

from ivetl.common import common
from ivetl.celery import app
from ivetl.models import PublishedArticle
from ivetl.pipelines.task import Task

@app.task
class InsertPredictionsTask(Task):
    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']
        total_count = task_args['count']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0
        for file in files:

            tlogger.info('Processing %s' % file)

            with open(file, 'r', encoding='utf-8') as tsv:
                for line in csv.DictReader(tsv, delimiter="\t"):

                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    meta_pmid = line['pmid']
                    doi = common.normalizedDoi(line['doi'])

                    try:
                        article = PublishedArticle.objects.get(publisher_id=publisher_id, article_doi=doi)

                        try:
                            meta_actual_ef = decimal.Decimal(line['actual_ef'])
                        except decimal.InvalidOperation:
                            meta_actual_ef = decimal.Decimal('0')

                        try:
                            meta_actual_citation_count = int(line['actual_citation_count'])
                        except ValueError:
                            meta_actual_citation_count = 0

                        try:
                            meta_predicted_ef = decimal.Decimal(line['predicted_ef'])
                        except decimal.InvalidOperation:
                            meta_predicted_ef = decimal.Decimal('0')

                        try:
                            meta_predicted_citation_count = int(line['predicted_citation_count'])
                        except ValueError:
                            meta_predicted_citation_count = 0

                        try:
                            meta_top_1 = int(line['top1 (Tier 5)'])
                        except ValueError:
                            meta_top_1 = 0

                        try:
                            meta_top_5 = int(line['top5 (Tier 4)'])
                        except ValueError:
                            meta_top_5 = 0

                        try:
                            meta_top_10 = int(line['top10 (Tier 3)'])
                        except ValueError:
                            meta_top_10 = 0

                        try:
                            meta_top_25 = int(line['top25 (Tier 2)'])
                        except ValueError:
                            meta_top_25 = 0

                        try:
                            meta_top_50 = int(line['top50 (Tier 1)'])
                        except ValueError:
                            meta_top_50 = 0

                        try:
                            meta_predicted_tiers = int(line['Predicted Tiers'])
                        except ValueError:
                            meta_predicted_tiers = 0

                        try:
                            meta_actual_tiers = int(line['Actual Tiers'])
                        except ValueError:
                            meta_actual_tiers = 0

                        article.update(
                            meta_pmid=meta_pmid,
                            meta_actual_ef=meta_actual_ef,
                            meta_actual_citation_count=meta_actual_citation_count,
                            meta_predicted_ef=meta_predicted_ef,
                            meta_predicted_citation_count=meta_predicted_citation_count,
                            meta_top_1=meta_top_1,
                            meta_top_5=meta_top_5,
                            meta_top_10=meta_top_10,
                            meta_top_25=meta_top_25,
                            meta_top_50=meta_top_50,
                            meta_predicted_tiers=meta_predicted_tiers,
                            meta_actual_tiers=meta_actual_tiers,
                        )

                    except PublishedArticle.DoesNotExist:
                        tlogger.info('Skipping %s, no existing record' % doi)

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, tlogger, show_alerts=task_args['show_alerts'])

        task_args['count'] = count
        return task_args
