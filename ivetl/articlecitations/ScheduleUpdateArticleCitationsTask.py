from __future__ import absolute_import

import datetime

from cassandra.cqlengine import connection

from celery import chain
import sendgrid

from ivetl.celery import app
from ivetl.common import common
from ivetl.common.Metadata import Metadata
from ivetl.common.BaseTask import BaseTask
from ivetl.articlecitations.GetScopusArticleCitationsTask import GetScopusArticleCitationsTask
from ivetl.articlecitations.InsertIntoCassandraDBTask import InsertIntoCassandraDBTask


@app.task
class ScheduleUpdateArticleCitationsTask(BaseTask):

    taskname = "ScheduleUpdateArticleCitations"
    vizor = common.AC

    def run(self):

        d = datetime.datetime.today()
        today = d.strftime('%Y%m%d')
        time = d.strftime('%H%M%S%f')

        connection.setup([common.CASSANDRA_IP], common.CASSANDRA_KEYSPACE_IV)

        publishers_metadata = Metadata.objects.all()

        for pm in publishers_metadata:

            publisher_id = pm.publisher_id

            workfolder = common.BASE_WORK_DIR + today + "/" + publisher_id + "/" + self.vizor + "/" + today + "_" + time

            #chain(GetScopusArticleCitationsTask.s(publisher_id, today, workfolder)).delay()
            chain(GetScopusArticleCitationsTask.s(publisher_id, today, workfolder, False, False) |
                  InsertIntoCassandraDBTask.s()).delay()







