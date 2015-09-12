from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.connectors import CrossrefConnector
from ivetl.models import Publisher_Metadata, Published_Article


@app.task
class GetCrossrefArticleCitationsTask(Task):

    def run_task(self, publisher_id, job_id, work_folder, tlogger, task_args):
        publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)

        # check for crossref credentials, fail if not...

        crossref = CrossrefConnector(publisher.crossref_username, publisher.crossref_password)
        articles = Published_Article.objects.filter(publisher_id=publisher_id)

        for article in articles:
            for citation_doi in crossref.get_citations(article.article_doi):

                # if already in cassandra
                    # add 'crossref' to citation_source
                # else
                    # get other article data from other crossref API
                    # insert new data

                pass

        return {self.INPUT_FILE: task_args[self.INPUT_FILE], self.COUNT: task_args[self.COUNT]}
