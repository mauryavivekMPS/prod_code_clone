import os
import csv
import codecs
import json
from datetime import datetime
from ivetl.celery import app
from ivetl.common.BaseTask import BaseTask
from ivetl.models import Published_Article, Publisher_Vizor_Updates, Publisher_Metadata, Article_Citations, Published_Article_Values, Issn_Journal
from ivetl.pipelines.task import Task


@app.task
class InsertCohortOwnerArticlesTask(Task):

    def run_task(self, publisher_id, job_id, work_folder, tlogger, task_args):

        limit = 10000000

        pm = Publisher_Metadata.objects.get(publisher_id=publisher_id)

        articles = Published_Article.objects.filter(publisher_id=pm.cohort_owner_publisher_id).limit(limit)
        count = 0
        for article in articles:
            count += 1
            tlogger.info("---")
            tlogger.info("%s of %s. Copying Article for %s / %s" % (count, len(articles), pm.cohort_owner_publisher_id, article.article_doi))

            article.publisher_id = publisher_id
            article.save()

        # count = 0
        # citations = Article_Citations.objects.filter(publisher_id=pm.cohort_owner_publisher_id).limit(limit)
        # for cite in citations:
        #     count += 1
        #     tlogger.info("---")
        #     tlogger.info("%s of %s. Copying Cite for %s / %s" % (count, len(citations), pm.cohort_owner_publisher_id, cite.citation_doi))
        #
        #     cite.publisher_id = publisher_id
        #     cite.save()

        self.pipeline_ended(publisher_id, job_id)
        return {self.COUNT: count}








