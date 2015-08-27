__author__ = 'nmehta'

from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
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

                      # new style imports, pipelines and then tasks, all from the same namespace
                      'ivetl.pipelines.publishedarticles',
                      'ivetl.pipelines.publishedarticles.tasks',
                      'ivetl.pipelines.customarticledata',
                      'ivetl.pipelines.customarticledata.tasks',
                      'ivetl.pipelines.articlecitations',
                      'ivetl.pipelines.articlecitations.tasks']
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
            protocol_version=3
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
