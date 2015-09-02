__author__ = 'nmehta'

from celery import Task
import logging
from os import makedirs
import datetime
from time import time
import csv
import sys

from ivetl.common import common
from ivetl.models.PipelineStatus import Pipeline_Status
from ivetl.models.PipelineTaskStatus import Pipeline_Task_Status


class BaseTask(Task):

    abstract = True
    vizor = ''

    PUBLISHER_ID = 'BaseTask.PublisherId'
    INPUT_FILE = 'BaseTask.InputFile'
    WORK_FOLDER = 'BaseTask.WorkFolder'
    JOB_ID = 'BaseTask.JobId'
    COUNT = 'BaseTask.Count'

    PL_STARTED = "started"
    PL_INPROGRESS = "in-progress"
    PL_COMPLETED = "completed"
    PL_ERROR = "error"

    def run(self, args):

        publisher = args[BaseTask.PUBLISHER_ID]
        workfolder = args[BaseTask.WORK_FOLDER]
        job_id = args[BaseTask.JOB_ID]

        task_workfolder, tlogger = self.setupTask(workfolder)
        csv.field_size_limit(sys.maxsize)

        t0 = time()
        self.taskStarted(publisher, job_id, task_workfolder, tlogger)

        return_args = self.run_task(publisher, job_id, task_workfolder, tlogger, args)

        self.taskEnded(publisher, job_id, t0, tlogger, return_args.get(BaseTask.COUNT))

        return return_args

    def run_task(self, publisher, job_id, workfolder, tlogger, args):
        raise NotImplementedError

    def getWorkFolder(self, day, publisher, job_id):
        return common.BASE_WORK_DIR + day + "/" + publisher + "/" + self.vizor + "/" + job_id

    def setupTask(self, workfolder):

        task_workfolder = workfolder + "/" + self.name
        makedirs(task_workfolder, exist_ok=True)
        tlogger = self.getTaskLogger(task_workfolder, self.name)

        return task_workfolder, tlogger

    def getTaskLogger(self, path, taskname):

        ti_logger = logging.getLogger(path)

        fh = logging.FileHandler(path + "/" + taskname + ".log", mode='w', encoding='utf-8')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)

        ti_logger.addHandler(fh)

        return ti_logger

    def pipelineStarted(self, publisher_id, pipeline_id, job_id, workfolder):

        start_date = datetime.datetime.today()

        p = Pipeline_Status()

        p.publisher_id = publisher_id
        p.pipeline_id = pipeline_id
        p.job_id = job_id
        p.start_time = start_date
        p.workfolder = workfolder
        p.updated = start_date
        p.save()

    def taskStarted(self, publisher, job_id, workfolder, tlogger):

        start_date = datetime.datetime.today()

        pts = Pipeline_Task_Status()
        pts.publisher_id = publisher
        pts.pipeline_id = self.vizor
        pts.job_id = job_id
        pts.task_id = self.name
        pts.start_time = start_date
        pts.status = self.PL_INPROGRESS
        pts.updated = start_date
        pts.workfolder = workfolder
        pts.save()

        ps = Pipeline_Status().objects.filter(publisher_id=publisher, pipeline_id=self.vizor, job_id=job_id).first()
        if ps is not None:
            ps.current_task = self.name
            ps.status = self.PL_INPROGRESS
            ps.updated = start_date
            ps.update()

        tlogger.info("Task " + self.name + " started for publisher " + publisher + " on " + str(start_date))

        return time()

    def taskEnded(self, publisher, job_id, start_time, tlogger, count=None):

        t1 = time()
        end_date = datetime.datetime.fromtimestamp(t1)
        duration_seconds = t1 - start_time

        pts = Pipeline_Task_Status()
        pts.publisher_id = publisher
        pts.pipeline_id = self.vizor
        pts.job_id = job_id
        pts.task_id = self.name
        pts.end_time = end_date
        pts.status = self.PL_COMPLETED
        pts.updated = end_date
        pts.duration_seconds = duration_seconds
        pts.update()

        if count is not None:
            tlogger.info("Rows Processed: " + str(count))

        tlogger.info("Time Taken: " + format(duration_seconds, '.2f') + " seconds / " + format((duration_seconds)/60, '.2f') + " minutes")

        return t1

    def pipelineCompleted(self, publisher_id, pipeline_id, job_id):

        end_date = datetime.datetime.today()

        p = Pipeline_Status().objects.filter(publisher_id=publisher_id, pipeline_id=pipeline_id, job_id=job_id).first()
        if p is not None:
            p.end_time = end_date
            p.duration_seconds = (end_date - p.start_time).total_seconds()
            p.status = self.PL_COMPLETED
            p.updated = end_date
            p.update()


    def on_failure(self, exc, task_id, args, kwargs, einfo):

        end_date = datetime.datetime.today()

        pts = Pipeline_Task_Status()
        pts.publisher_id = args[0][BaseTask.PUBLISHER_ID]
        pts.pipeline_id = self.vizor
        pts.job_id = args[0][BaseTask.JOB_ID]
        pts.task_id = self.name
        pts.end_time = end_date
        pts.status = self.PL_ERROR
        pts.error_details = str(exc)
        pts.updated = end_date
        pts.update()

        ps = Pipeline_Status().objects.filter(publisher_id=args[0][BaseTask.PUBLISHER_ID],
                                              pipeline_id=self.vizor,
                                              job_id=args[0][BaseTask.JOB_ID]).first()

        if ps is not None:
            ps.end_time = end_date
            ps.duration_seconds = (end_date - ps.start_time).total_seconds()
            ps.status = self.PL_ERROR
            ps.error_details = str(exc)
            ps.updated = end_date
            ps.update()

        day = end_date.strftime('%Y.%m.%d')
        subject = "ERROR! " + day + " - " + self.vizor + " - " + self.name

        body = "<b>Vizor:</b> <br>"
        body += self.vizor

        body += "<br><br><b>Task:</b> <br>"
        body += self.name

        body += "<br><br><b>Arguments:</b> <br>"
        body += str(args)

        body += "<br><br><b>Exception:</b> <br>"
        body += str(exc)

        body += "<br><br><b>Traceback:</b> <br>"
        body += einfo.traceback

        body += "<br><br><b>Command To Rerun Task:</b> <br>"
        body += self.__class__.__name__ + ".s" + str(args) + ".delay()"

        common.send_email(subject, body)

    def on_success(self, retval, task_id, args, kwargs):

        day = datetime.datetime.today().strftime('%Y.%m.%d')
        subject = "SUCCESS: " + day + " - " + self.vizor + " - " + self.name

        body = "<b>Vizor:</b> <br>"
        body += self.vizor

        body += "<br><br><b>Task:</b> <br>"
        body += self.name

        body += "<br><br><b>Arguments:</b> <br>"
        body += str(args)

        body += "<br><br><b>Return Value:</b> <br>"
        body += str(retval)

        common.send_email(subject, body)




