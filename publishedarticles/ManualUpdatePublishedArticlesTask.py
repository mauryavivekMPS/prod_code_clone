from __future__ import absolute_import

import datetime

from cassandra.cqlengine import connection

from celery import chain

from ivetl.celery import app
from ivetl.common import common
from ivetl.common.Metadata import Metadata
from ivetl.common.BaseTask import BaseTask
from ivetl.publishedarticles.GetPublishedArticlesTask import GetPublishedArticlesTask
from ivetl.publishedarticles.ScopusIdLookupTask import ScopusIdLookupTask
from ivetl.publishedarticles.HWMetadataLookupTask import HWMetadataLookupTask
from ivetl.publishedarticles.InsertIntoCassandraDBTask import InsertIntoCassandraDBTask


@app.task
class ManualUpdatePublishedArticlesTask(BaseTask):

    taskname = "ManualUpdatePublishedArticles"
    vizor = common.PA

    def run(self, publisher, reprocessall):

        d = datetime.datetime.today()
        today = d.strftime('%Y%m%d')
        time = d.strftime('%H%M%S%f')

        connection.setup([common.CASSANDRA_IP], common.CASSANDRA_KEYSPACE_IV)

        pm = Metadata.objects.filter(publisher_id=publisher).first()

        publisher_id = pm.publisher_id
        issns = pm.issn.split(",")

        if reprocessall:
            start_publication_date = datetime.date(2011, 1, 1)
        else:
            start_publication_date = pm.last_updated_date

        workfolder = common.BASE_WORK_DIR + today + "/" + publisher_id + "/" + self.vizor + "/" + today + "_" + time

        chain(GetPublishedArticlesTask.s(publisher_id, issns, start_publication_date, today, workfolder) |
              ScopusIdLookupTask.s() |
              HWMetadataLookupTask.s() |
              InsertIntoCassandraDBTask.s()).delay()







