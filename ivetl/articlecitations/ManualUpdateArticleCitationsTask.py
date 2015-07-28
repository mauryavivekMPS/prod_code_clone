from __future__ import absolute_import

import datetime

from celery import chain

from ivetl.celery import app
from ivetl.common import common
from ivetl.common.Metadata import Metadata
from ivetl.common.BaseTask import BaseTask
from ivetl.articlecitations.GetScopusArticleCitationsTask import GetScopusArticleCitationsTask
from ivetl.articlecitations.InsertIntoCassandraDBTask import InsertIntoCassandraDBTask


@app.task
class ManualUpdateArticleCitationsTask(BaseTask):

    taskname = "ManualUpdateArticleCitations"
    vizor = common.AC

    def run(self, publisher, reprocessall, reprocesserrorsonly):

        d = datetime.datetime.today()
        today = d.strftime('%Y%m%d')
        time = d.strftime('%H%M%S%f')

        workfolder = common.BASE_WORK_DIR + today + "/" + publisher + "/" + self.vizor + "/" + today + "_" + time

        chain(GetScopusArticleCitationsTask.s(publisher, today, workfolder, reprocessall, reprocesserrorsonly) |
              InsertIntoCassandraDBTask.s()).delay()







