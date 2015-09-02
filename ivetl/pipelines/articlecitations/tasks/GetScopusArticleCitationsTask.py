__author__ = 'nmehta'

import codecs
import json
from ivetl.celery import app
from ivetl.connectors.MaxTriesAPIError import MaxTriesAPIError
from ivetl.models.PublishedArticle import Published_Article
from ivetl.connectors.ScopusConnector import ScopusConnector
from ivetl.models.PublisherMetadata import Publisher_Metadata
from ivetl.pipelines.task import Task


@app.task
class GetScopusArticleCitationsTask(Task):

    REPROCESS_ERRORS = 'GetScopusArticleCitations.ReprocessErrors'
    QUERY_LIMIT = 500000
    MAX_ERROR_COUNT = 100

    def run_task(self, publisher_id, job_id, work_folder, tlogger, task_args):

        reprocesserrorsonly = task_args[GetScopusArticleCitationsTask.REPROCESS_ERRORS]

        target_file_name = work_folder + "/" + publisher_id + "_" + "articlecitations" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\t'
                          'DOI\t'
                          'DATA\n')

        count = 0
        error_count = 0

        pm = Publisher_Metadata.objects.get(publisher_id=publisher_id)
        connector = ScopusConnector(pm.scopus_api_keys)

        articles = Published_Article.objects.filter(publisher_id=publisher_id).limit(self.QUERY_LIMIT)
        total_articles = len(articles)

        for article in articles:

            count += 1

            tlogger.info("---")
            tlogger.info(str(count) + " of " + str(total_articles) + ". Looking Up Citations for " + publisher_id + " / " + article.article_doi)

            if article.article_scopus_id is None or article.article_scopus_id == '':
                tlogger.info("Skipping - No Scopus Id")
                continue

            if reprocesserrorsonly:
                if article.citations_lookup_error is not True:
                    tlogger.info("Skipping - Only processing Articles with error in looking up citations")
                    continue

            citations = []
            try:
                citations = connector.getScopusCitations(article.article_scopus_id, tlogger)

            except MaxTriesAPIError:
                tlogger.info("Scopus API failed for " + article.article_scopus_id)
                error_count += 1

                pa = Published_Article()
                pa['publisher_id'] = publisher_id
                pa['article_doi'] = article.article_doi
                pa['citations_lookup_error'] = True
                pa.update()

            if error_count >= self.MAX_ERROR_COUNT:
                    raise MaxTriesAPIError(self.MAX_ERROR_COUNT)

            row = """%s\t%s\t%s\n""" % (
                                publisher_id,
                                article.article_doi,
                                json.dumps(citations))

            target_file.write(row)
            target_file.flush()

            tlogger.info(str(len(citations)) + " citations retrieved.")

        target_file.close()

        return {self.INPUT_FILE: target_file_name, self.COUNT: count}








