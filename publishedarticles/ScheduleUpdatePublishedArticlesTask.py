from __future__ import absolute_import

import datetime

from cassandra.cqlengine import connection

from celery import chain
import sendgrid

from ivetl.celery import app
from ivetl.common import common
from ivetl.common.Metadata import Metadata
from ivetl.common.BaseTask import BaseTask
from ivetl.publishedarticles.GetPublishedArticlesTask import GetPublishedArticlesTask
from ivetl.publishedarticles.ScopusIdLookupTask import ScopusIdLookupTask
from ivetl.publishedarticles.HWMetadataLookupTask import HWMetadataLookupTask
from ivetl.publishedarticles.InsertIntoCassandraDBTask import InsertIntoCassandraDBTask


@app.task
class ScheduleUpdatePublishedArticlesTask(BaseTask):

    taskname = "ScheduleUpdatePublishedArticles"
    vizor = common.PA

    def run(self):

        d = datetime.datetime.today()
        today = d.strftime('%Y%m%d')
        time = d.strftime('%H%M%S%f')

        connection.setup([common.CASSANDRA_IP], common.CASSANDRA_KEYSPACE_IV)

        publishers_metadata = Metadata.objects.all()

        for pm in publishers_metadata:

            publisher_id = pm.publisher_id
            issns = pm.issn.split(",")
            start_publication_date = pm.last_updated_date

            workfolder = common.BASE_WORK_DIR + today + "/" + publisher_id + "/" + self.vizor + "/" + today + "_" + time

            chain(GetPublishedArticlesTask.s(publisher_id, issns, start_publication_date, today, workfolder) |
                  ScopusIdLookupTask.s() |
                  HWMetadataLookupTask.s() |
                  InsertIntoCassandraDBTask.s()).delay()







