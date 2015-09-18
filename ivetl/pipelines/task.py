__author__ = 'nmehta, johnm'

import datetime
from time import time
import csv
import sys
from ivetl.common import common
from ivetl.pipelines.base_task import BaseTask
from ivetl.models import Pipeline_Status, Pipeline_Task_Status


class Task(BaseTask):
    abstract = True
    pipeline_name = ''

    def run(self, task_args):
        new_task_args = task_args.copy()

        # pull the standard args out of task args
        publisher_id = new_task_args.pop('publisher_id')
        work_folder = new_task_args.pop('work_folder')
        job_id = new_task_args.pop('job_id')
        pipeline_name = new_task_args.pop('pipeline_name')

        # save the pipeline name
        self.pipeline_name = pipeline_name

        # set up the directory for this task
        task_work_folder, tlogger = self.setup_task(work_folder)
        csv.field_size_limit(sys.maxsize)

        # run the task
        t0 = time()
        self.on_task_started(pipeline_name, publisher_id, job_id, task_work_folder, tlogger)
        task_result = self.run_task(publisher_id, job_id, task_work_folder, tlogger, new_task_args)
        self.on_task_ended(pipeline_name, publisher_id, job_id, t0, tlogger, task_result.get('count'))

        # construct a new task args with the result
        task_result['publisher_id'] = publisher_id
        task_result['work_folder'] = work_folder
        task_result['job_id'] = job_id
        task_result['pipeline_name'] = pipeline_name

        return task_result

    def run_task(self, publisher_id, job_id, work_folder, tlogger, task_args):
        raise NotImplementedError

    def on_task_started(self, pipeline_name, publisher_id, job_id, work_folder, tlogger):
        start_date = datetime.datetime.today()

        pts = Pipeline_Task_Status()
        pts.publisher_id = publisher_id
        pts.pipeline_id = pipeline_name
        pts.job_id = job_id
        pts.task_id = self.short_name
        pts.start_time = start_date
        pts.status = self.PL_INPROGRESS
        pts.updated = start_date
        pts.workfolder = work_folder
        pts.save()

        Pipeline_Status.objects(publisher_id=publisher_id, pipeline_id=pipeline_name, job_id=job_id).update(
            current_task=self.name,
            status=self.PL_INPROGRESS,
            updated=start_date
        )

        tlogger.info("Task %s started for publisher %s on %s" % (self.short_name, publisher_id, start_date))

    def on_task_ended(self, pipeline_name, publisher_id, job_id, start_time, tlogger, count=None):
        t1 = time()
        end_date = datetime.datetime.fromtimestamp(t1)
        duration_seconds = t1 - start_time

        pts = Pipeline_Task_Status()
        pts.publisher_id = publisher_id
        pts.pipeline_id = pipeline_name
        pts.job_id = job_id
        pts.task_id = self.short_name
        pts.end_time = end_date
        pts.status = self.PL_COMPLETED
        pts.updated = end_date
        pts.duration_seconds = duration_seconds
        pts.update()

        if count:
            tlogger.info("Rows Processed: %s" % count)

        tlogger.info("Time Taken: " + format(duration_seconds, '.2f') + " seconds / " + format(duration_seconds/60, '.2f') + " minutes")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        end_date = datetime.datetime.today()
        task_args = args[0]
        pipeline_name = task_args['pipeline_name']
        publisher_id = task_args['publisher_id']
        job_id = task_args['job_id']

        pts = Pipeline_Task_Status()
        pts.publisher_id = publisher_id
        pts.pipeline_id = pipeline_name
        pts.job_id = job_id
        pts.task_id = self.short_name
        pts.end_time = end_date
        pts.status = self.PL_ERROR
        pts.error_details = str(exc)
        pts.updated = end_date
        pts.update()

        try:
            ps = Pipeline_Status.objects.get(publisher_id=publisher_id, pipeline_id=pipeline_name, job_id=job_id)
            ps.update(
                end_time=end_date,
                duration_seconds=(end_date - ps.start_time).total_seconds(),
                status=self.PL_ERROR,
                error_details=str(exc),
                updated=end_date
            )
        except Pipeline_Status.DoesNotExist:
            # don't write any status if a row doesn't already exist
            pass

        day = end_date.strftime('%Y.%m.%d')
        subject = "ERROR! " + day + " - " + pipeline_name + " - " + self.short_name
        body = "<b>Pipeline:</b> <br>"
        body += pipeline_name
        body += "<br><br><b>Task:</b> <br>"
        body += self.short_name
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
        task_args = args[0]
        pipeline_name = task_args['pipeline_name']
        day = datetime.datetime.today().strftime('%Y.%m.%d')
        subject = "SUCCESS: " + day + " - " + pipeline_name + " - " + self.short_name
        body = "<b>Pipeline:</b> <br>"
        body += pipeline_name
        body += "<br><br><b>Task:</b> <br>"
        body += self.short_name
        body += "<br><br><b>Arguments:</b> <br>"
        body += str(args)
        body += "<br><br><b>Return Value:</b> <br>"
        body += str(retval)
        common.send_email(subject, body)

    # !! TODO: this needs to be moved!
    def pipeline_ended(self, publisher_id, job_id):
        end_date = datetime.datetime.today()
        p = Pipeline_Status().objects.filter(publisher_id=publisher_id, pipeline_id=self.pipeline_name, job_id=job_id).first()
        if p is not None:
            p.end_time = end_date
            p.duration_seconds = (end_date - p.start_time).total_seconds()
            p.status = self.PL_COMPLETED
            p.updated = end_date
            p.update()
