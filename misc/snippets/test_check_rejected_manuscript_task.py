import os, sys
from getopt import getopt
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
os.sys.path.append(os.environ['IVETL_ROOT'])
from ivetl.common import common # from ivetl import utils
from ivetl.models import PublishedArticle, RejectedArticles, PipelineStatus
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
opts, args = getopt(sys.argv[1:], 'p:', ['help','publisher',])
publisher_id = None
for opt in opts:
    publisher_id = opt[1] if opt[0] == '-p' else publisher_id

open_cassandra_connection()
# lines 17-87, ivetl/pipelines/published_articles/tasks/check_rejected_manuscript.py
# commented out: 20-21, 42-43, modified slightly: 59,
cluster = Cluster(common.CASSANDRA_IP_LIST)
session = cluster.connect()

# total_count = utils.get_record_count_estimate(publisher_id, product_id, pipeline_id, self.short_name)
# self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

rejected_articles_sql = """
  select crossref_doi, manuscript_id, editor, date_of_rejection, status
  from impactvizor.rejected_articles
  where publisher_id = %s
  limit 1000000
"""

rejected_articles_statement = SimpleStatement(rejected_articles_sql, fetch_size=1000)

rm_map = {}
for rejected_article_row in session.execute(rejected_articles_statement, (publisher_id,)):
    if rejected_article_row.status != 'Not Published':
        rm_map[rejected_article_row.crossref_doi] = (
            rejected_article_row.manuscript_id,
            rejected_article_row.editor,
            rejected_article_row.date_of_rejection
        )

article_limit = 1000000
# if 'max_articles_to_process' in task_args and task_args['max_articles_to_process']:
#    article_limit = task_args['max_articles_to_process']

all_articles_sql = """
  select article_doi, from_rejected_manuscript, rejected_manuscript_id, rejected_manuscript_editor, date_of_rejection
  from impactvizor.published_article
  where publisher_id = %s
  limit %s
"""

all_articles_statement = SimpleStatement(all_articles_sql, fetch_size=1000)

count = 0
for article_row in session.execute(all_articles_statement, (publisher_id, article_limit)):

    count += 1 # = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

    print("row %s. Looking up rejected manuscript for %s / %s (est)" % (count, publisher_id, article_row.article_doi)) # tlogger.info("%s of %s. Looking up rejected manuscript for %s / %s (est)" % (count, total_count, publisher_id, article_row.article_doi))

    rm = rm_map.get(article_row.article_doi)
    if rm:
        manuscript_id, editor, date_of_rejection = rm
        PublishedArticle.objects(
            publisher_id=publisher_id,
            article_doi=common.normalizedDoi(article_row.article_doi),
        ).update(
            from_rejected_manuscript=True,
            rejected_manuscript_id=manuscript_id,
            rejected_manuscript_editor=editor,
            date_of_rejection=date_of_rejection,
        )
        print("Article sourced from rejected manuscript") # tlogger.info("Article sourced from rejected manuscript")
    elif article_row.from_rejected_manuscript:
        # published_article row was previously matched,
        # however rejected manuscript is now matched to another article
        # cleanup / reset previous rejected article match data
        PublishedArticle.objects(
          publisher_id=publisher_id,
          article_doi=common.normalizedDoi(article_row.article_doi),
        ).update(
            from_rejected_manuscript=False,
            rejected_manuscript_id=None,
            rejected_manuscript_editor=None,
            date_of_rejection=None,
        )
        print("Article previously matched to rejected manuscript, but no longer does.") # tlogger.info("Article previously matched to rejected manuscript, but no longer does.")

close_cassandra_connection()
