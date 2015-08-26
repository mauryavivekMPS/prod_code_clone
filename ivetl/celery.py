__author__ = 'nmehta'

from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
from cassandra.policies import DCAwareRoundRobinPolicy
from cassandra.cqlengine import connection
from ivetl.common import common


app = Celery('ivetl',
             include=['ivetl.rat.ValidateInputFileTask',
                      'ivetl.rat.MonitorIncomingFileTask',
                      'ivetl.rat.PrepareInputFileTask',
                      'ivetl.rat.XREFPublishedArticleSearchTask',
                      'ivetl.rat.SelectPublishedArticleTask',
                      'ivetl.rat.ScopusCitationLookupTask',
                      'ivetl.rat.PrepareForDBInsertTask',
                      'ivetl.rat.InsertIntoCassandraDBTask',
                      'ivetl.rat.XREFJournalCatalogTask',
                      'ivetl.publishedarticles.ScheduleUpdatePublishedArticlesTask',
                      'ivetl.publishedarticles.ManualUpdatePublishedArticlesTask',
                      'ivetl.publishedarticles.GetPublishedArticlesTask',
                      'ivetl.publishedarticles.ScopusIdLookupTask',
                      'ivetl.publishedarticles.HWMetadataLookupTask',
                      'ivetl.publishedarticles.InsertIntoCassandraDBTask',
                      'ivetl.articlecitations.ScheduleUpdateArticleCitationsTask',
                      'ivetl.articlecitations.ManualUpdateArticleCitationsTask',
                      'ivetl.articlecitations.GetScopusArticleCitationsTask',
                      'ivetl.articlecitations.InsertIntoCassandraDBTask',
                      'ivetl.articlecitations.InsertArticleCitationPlaceholderTask']
            )

# Optional configuration, see the application user guide.
app.config_from_object('ivetl.celeryconfig')


# Initialize Database Pool
@worker_process_init.connect
def init_worker(**kwargs):
    if common.IS_LOCAL:
        connection.setup(
            [common.CASSANDRA_IP],
            common.CASSANDRA_KEYSPACE_IV,
            protocol_version=3,
            load_balancing_policy=DCAwareRoundRobinPolicy(local_dc='local')
        )
    else:
        connection.setup(
            [common.CASSANDRA_IP],
            common.CASSANDRA_KEYSPACE_IV
        )


@worker_process_shutdown.connect
def shutdown_worker(pid, exitcode, **kwargs):
    connection.get_cluster().shutdown()


if __name__ == '__main__':
    app.start()
