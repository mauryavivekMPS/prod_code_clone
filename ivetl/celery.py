from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
from cassandra.cqlengine import connection
from ivetl.common import common

from celery.concurrency import asynpool
# allow increased timeouts for high-latency local development environments
if common.IS_LOCAL:
    asynpool.PROC_ALIVE_TIMEOUT = 45.0

app = Celery('ivetl')

# Optional configuration, see the application user guide.
app.config_from_object('ivetl.celeryconfig')


def open_cassandra_connection():
    if common.IS_LOCAL:
        connection.setup(
            common.CASSANDRA_IP_LIST,
            common.CASSANDRA_KEYSPACE_IV,
            control_connection_timeout=30,
            connect_timeout=120
        )
    else:
        connection.setup(
            common.CASSANDRA_IP_LIST,
            common.CASSANDRA_KEYSPACE_IV
        )


def close_cassandra_connection():
    connection.get_cluster().shutdown()


# Initialize Database Pool
@worker_process_init.connect
def init_worker(**kwargs):
    open_cassandra_connection()


@worker_process_shutdown.connect
def shutdown_worker(pid, exitcode, **kwargs):
    close_cassandra_connection()


if __name__ == '__main__':
    app.start()
