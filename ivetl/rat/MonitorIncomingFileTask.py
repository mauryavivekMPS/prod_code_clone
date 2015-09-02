from __future__ import absolute_import

import os
import os.path
import shutil
import datetime
from os import makedirs

from celery import chain
import sendgrid

from ivetl.common import common
from ivetl.celery import app
from ivetl.common.BaseTask import BaseTask
from ivetl.rat.ValidateInputFileTask import ValidateInputFileTask
from ivetl.rat.PrepareInputFileTask import PrepareInputFileTask
from ivetl.rat.XREFPublishedArticleSearchTask import XREFPublishedArticleSearchTask
from ivetl.rat.SelectPublishedArticleTask import SelectPublishedArticleTask
from ivetl.rat.ScopusCitationLookupTask import ScopusCitationLookupTask
from ivetl.rat.PrepareForDBInsertTask import PrepareForDBInsertTask
from ivetl.rat.InsertIntoCassandraDBTask import InsertIntoCassandraDBTask


@app.task
class MonitorIncomingFileTask(BaseTask):

    taskname = "MonitorIncomingFile"
    vizor = common.RAT

    def run(self):

        d = datetime.datetime.today()
        today = d.strftime('%Y%m%d')
        time = d.strftime('%H%M%S%f')

        for publisher_dir in os.listdir(common.BASE_INCOMING_DIR):
            if os.path.isdir(os.path.join(common.BASE_INCOMING_DIR, publisher_dir)):

                srcpath = common.BASE_INCOMING_DIR + '/' + publisher_dir + "/" + common.RAT_DIR
                files = [f for f in os.listdir(srcpath) if os.path.isfile(os.path.join(srcpath, f))]

                if len(files) > 0:

                    subject = "Rejected Article Tracker - " + today + " - Processing started for " + publisher_dir
                    text = "Processing files for " + publisher_dir
                    common.send_email(subject, text)

                    workfolder = common.BASE_WORK_DIR + "/" + publisher_dir + "/" + self.vizor + "/" + today + "_" + time
                    dstworkpath = workfolder + "/" + self.taskname
                    makedirs(dstworkpath, exist_ok=True)

                    tlogger = self.getTaskLogger(dstworkpath, self.taskname)

                    dstfiles = []
                    for file in files:

                        dstfile = dstworkpath + "/" + file
                        if os.path.exists(dstfile):
                            os.remove(dstfile)

                        shutil.move(srcpath + "/" + file, dstfile)
                        dstfiles.append(dstfile)

                        tlogger.info("Copied File:             " + file)

                    chain(ValidateInputFileTask.s(dstfiles, publisher_dir, today, workfolder) |
                          PrepareInputFileTask.s() |
                          XREFPublishedArticleSearchTask.s() |
                          SelectPublishedArticleTask.s() |
                          ScopusCitationLookupTask.s() |
                          PrepareForDBInsertTask.s() |
                          InsertIntoCassandraDBTask.s()).delay()







