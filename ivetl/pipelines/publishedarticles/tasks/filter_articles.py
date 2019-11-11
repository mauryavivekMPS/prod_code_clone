import codecs
import csv
import json
import os

from ivetl.article_skipper import ArticleSkipper
from ivetl.celery import app
from ivetl.common import common
from ivetl.models import PublishedArticle, ArticleCitations, PublishedArticleByCohort, ArticleUsage, PublishedArticleValues
from ivetl.pipelines.task import Task


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
                doi = common.normalizedDoi(line[1])
                issn = line[2]
                data = json.loads(line[3])

                if skipper.should_skip_article_for_journal(doi, issn, data):
                    tlogger.info('Filtering %s' % doi)

                    try:
                        PublishedArticle.objects.get(publisher_id=publisher_id, article_doi=doi).delete()

                        tlogger.info('Deleting previously fetched article that we are now skipping %s' % doi)

                        # if we have found a matching article then we should make sure it's cleaned out from other tables
                        ArticleCitations.objects.filter(publisher_id=publisher_id, article_doi=doi).delete()
                        PublishedArticleByCohort.filter(publisher_id=publisher_id, is_cohort=True, article_doi=doi).delete()
                        PublishedArticleByCohort.filter(publisher_id=publisher_id, is_cohort=False, article_doi=doi).delete()
                        ArticleUsage.filter(publisher_id=publisher_id, article_doi=doi).delete()
                        PublishedArticleValues.filter(publisher_id=publisher_id, article_doi=doi).delete()

                    except PublishedArticle.DoesNotExist:
                        pass

                else:
                    target_file.write('\t'.join([publisher_id, doi, issn, json.dumps(data)]) + '\n')

        target_file.close()

        task_args['input_file'] = target_file_name
        task_args['count'] = count

        return task_args
