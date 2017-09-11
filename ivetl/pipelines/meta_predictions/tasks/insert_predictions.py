import csv
import decimal
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import PublishedArticle


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
                for line in csv.reader(tsv, delimiter="\t"):

                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    # skip header row
                    if count == 1:
                        continue

                    meta_pmid = line[0]
                    doi = line[1]

                    try:
                        meta_actual_ef = decimal.Decimal(line[6])
                    except decimal.InvalidOperation:
                        meta_actual_ef = decimal.Decimal('0')

                    try:
                        meta_actual_citation_count = int(line[7])
                    except ValueError:
                        meta_actual_citation_count = 0

                    try:
                        meta_predicted_ef = decimal.Decimal(line[8])
                    except decimal.InvalidOperation:
                        meta_predicted_ef = decimal.Decimal('0')

                    try:
                        meta_predicted_citation_count = int(line[9])
                    except ValueError:
                        meta_predicted_citation_count = 0

                    try:
                        meta_top_1 = int(line[10])
                    except ValueError:
                        meta_top_1 = 0

                    try:
                        meta_top_5 = int(line[11])
                    except ValueError:
                        meta_top_5 = 0

                    try:
                        meta_top_10 = int(line[12])
                    except ValueError:
                        meta_top_10 = 0

                    try:
                        meta_top_25 = int(line[13])
                    except ValueError:
                        meta_top_25 = 0

                    try:
                        meta_top_50 = int(line[14])
                    except ValueError:
                        meta_top_50 = 0

                    try:
                        meta_predicted_tiers = int(line[15])
                    except ValueError:
                        meta_predicted_tiers = 0

                    try:
                        meta_actual_tiers = int(line[16])
                    except ValueError:
                        meta_actual_tiers = 0

                    PublishedArticle.objects(
                        publisher_id=publisher_id,
                        article_doi=doi,
                    ).update(
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

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, tlogger, show_alerts=task_args['show_alerts'])

        task_args['count'] = count
        return task_args
