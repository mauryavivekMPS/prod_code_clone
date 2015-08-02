from __future__ import absolute_import

from celery import Task
import logging
from os import makedirs
import datetime
from time import time

from ivetl.common import common


class BaseTask(Task):

    abstract = True
    taskname = ''
    vizor = ''

    PUBLISHER_ID = 'BaseTask.PublisherId'
    INPUT_FILE = 'BaseTask.InputFile'
    WORK_FOLDER = 'BaseTask.WorkFolder'
    JOB_ID = 'BaseTask.JobId'

    def getWorkFolder(self, day, publisher, job_id):
        return common.BASE_WORK_DIR + day + "/" + publisher + "/" + self.vizor + "/" + job_id

    def setupTask(self, workfolder):

        task_workfolder = workfolder + "/" + self.taskname
        makedirs(task_workfolder, exist_ok=True)
        tlogger = self.getTaskLogger(task_workfolder, self.taskname)

        return task_workfolder, tlogger

    def taskStarted(self, publisher, job_id):

        # Update Task Status In DB
        # To Do
        return time()

    def taskEnded(self, publisher, job_id, start_time, tlogger, count=None):

        t1 = time()
        if count is not None:
            tlogger.info("Rows Processed: " + str(count))

        tlogger.info("Time Taken: " + format(t1-start_time, '.2f') + " seconds / " + format((t1-start_time)/60, '.2f') + " minutes")

    def getTaskLogger(self, path, taskname):

        ti_logger = logging.getLogger(path)

        fh = logging.FileHandler(path + "/" + taskname + ".log", mode='w', encoding='utf-8')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)

        ti_logger.addHandler(fh)

        return ti_logger


    def on_failure(self, exc, task_id, args, kwargs, einfo):

        day = datetime.datetime.today().strftime('%Y.%m.%d')
        subject = "ERROR! " + day + " - " + self.vizor + " - " + self.taskname

        body = "<b>Vizor:</b> <br>"
        body += self.vizor

        body += "<br><br><b>Task:</b> <br>"
        body += self.taskname

        body += "<br><br><b>Arguments:</b> <br>"
        body += str(args)

        body += "<br><br><b>Exception:</b> <br>"
        body += str(exc)

        body += "<br><br><b>Traceback:</b> <br>"
        body += einfo.traceback

        body += "<br><br><b>Command To Rerun Task:</b> <br>"
        body += self.__class__.__name__ + ".s" + str(args) + ".delay()"

        common.sendEmail(subject, body)


    def on_success(self, retval, task_id, args, kwargs):

        day = datetime.datetime.today().strftime('%Y.%m.%d')
        subject = "SUCCESS: " + day + " - " + self.vizor + " - " + self.taskname

        body = "<b>Vizor:</b> <br>"
        body += self.vizor

        body += "<br><br><b>Task:</b> <br>"
        body += self.taskname

        body += "<br><br><b>Arguments:</b> <br>"
        body += str(args)

        body += "<br><br><b>Return Value:</b> <br>"
        body += str(retval)

        common.sendEmail(subject, body)




