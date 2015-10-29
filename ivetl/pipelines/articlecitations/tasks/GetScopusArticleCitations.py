import os
import json
import codecs
from ivetl.celery import app
from ivetl.connectors import ScopusConnector, MaxTriesAPIError
from ivetl.models import Publisher_Metadata, Published_Article
from ivetl.pipelines.task import Task
from ivetl.common import common


@app.task
class GetScopusArticleCitations(Task):
    REPROCESS_ERRORS = 'GetScopusArticleCitations.ReprocessErrors'
    QUERY_LIMIT = 50000000
    MAX_ERROR_COUNT = 100

    def run_task(self, publisher_id, job_id, work_folder, tlogger, task_args):

        reprocesserrorsonly = task_args[GetScopusArticleCitations.REPROCESS_ERRORS]
        product = common.PRODUCT_BY_ID[task_args['product_id']]

        target_file_name = os.path.join(work_folder, "%s_articlecitations_target.tab" % publisher_id)
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\t'
                          'DOI\t'
                          'DATA\n')

        pm = Publisher_Metadata.objects.get(publisher_id=publisher_id)
        connector = ScopusConnector(pm.scopus_api_keys)

        if product['cohort']:
            articles = Published_Article.objects.filter(publisher_id=publisher_id, is_cohort=True).limit(self.QUERY_LIMIT)
        else:
            articles = Published_Article.objects.filter(publisher_id=publisher_id, is_cohort=False).limit(self.QUERY_LIMIT)

        count = 0
        error_count = 0

        for article in articles:

            count += 1
            tlogger.info("---")
            tlogger.info("%s of %s. Looking Up citations for %s / %s" % (count, len(articles), publisher_id, article.article_doi))

            if article.article_scopus_id is None or article.article_scopus_id == '':
                tlogger.info("Skipping - No Scopus Id")
                continue

            if reprocesserrorsonly:
                if article.citations_lookup_error is not True:
                    tlogger.info("Skipping - Only processing Articles with error in looking up citations")
                    continue

            citations = []
            try:
                citations = connector.get_citations(article.article_scopus_id, article.is_cohort, tlogger)

            except MaxTriesAPIError:
                tlogger.info("Scopus API failed for %s" % article.article_scopus_id)
                error_count += 1

                pa = Published_Article()
                pa['publisher_id'] = publisher_id
                pa['article_doi'] = article.article_doi
                pa['citations_lookup_error'] = True
                pa.update()

            if error_count >= self.MAX_ERROR_COUNT:
                    raise MaxTriesAPIError(self.MAX_ERROR_COUNT)

            row = "%s\t%s\t%s\n" % (publisher_id, article.article_doi, json.dumps(citations))

            target_file.write(row)
            target_file.flush()

            tlogger.info("%s citations retrieved." % len(citations))

        target_file.close()

        task_args[self.INPUT_FILE] = target_file_name
        task_args[self.COUNT] = count

        return task_args









