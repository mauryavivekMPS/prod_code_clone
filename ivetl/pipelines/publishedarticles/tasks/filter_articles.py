import os
import csv
import codecs
import json
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.article_skipper import ArticleSkipper
from ivetl.common import common


@app.task
class FilterArticlesTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        product = common.PRODUCT_BY_ID[product_id]

        file = task_args['input_file']
        total_count = task_args['count']

        target_file_name = os.path.join(work_folder, publisher_id + "_" + "filteredarticles" + "_" + "target.tab")
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('\t'.join(['PUBLISHER_ID', 'DOI', 'ISSN', 'DATA']) + '\n')

        count = 0
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        skipper = ArticleSkipper(publisher_id, product['cohort'])

        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                if count == 1:
                    continue

                publisher_id = line[0]
                doi = line[1]
                issn = line[2]
                data = json.loads(line[3])

                if skipper.should_skip_article_for_journal(doi, issn, data):
                    tlogger.info('Filtering %s' % doi)
                else:
                    target_file.write('\t'.join([publisher_id, doi, issn, json.dumps(data)]) + '\n')

        target_file.close()

        task_args['input_file'] = target_file_name
        task_args['count'] = count

        return task_args
