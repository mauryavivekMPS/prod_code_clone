__author__ = 'nmehta, johnm'

import datetime
from ivetl.common import common
from ivetl.pipelines.base_task import BaseTask
from ivetl.models import Pipeline_Status, Pipeline_Task_Status


class Pipeline(BaseTask):
    abstract = True

    def pipeline_started(self, publisher_id, pipeline_id, job_id, workfolder):

        start_date = datetime.datetime.today()

        p = Pipeline_Status()

        p.publisher_id = publisher_id
        p.pipeline_id = pipeline_id
        p.job_id = job_id
        p.start_time = start_date
        p.workfolder = workfolder
        p.updated = start_date
        p.save()

    def on_failure(self, exc, task_id, args, kwargs, einfo):

        end_date = datetime.datetime.today()

        pts = Pipeline_Task_Status()
        # pts.publisher_id = args[0][self.PUBLISHER_ID]
        pts.publisher_id = 'test'  # TODO: FIX ME!
        pts.pipeline_id = self.vizor
        # pts.job_id = args[0][BaseTask.JOB_ID]
        pts.job_id = 'no-job-id-yet'  # TODO: FIX ME TOO!
        pts.task_id = self.name
        pts.end_time = end_date
        pts.status = self.PL_ERROR
        pts.error_details = str(exc)
        pts.updated = end_date
        # pts.update()

        # ps = Pipeline_Status().objects.filter(publisher_id=args[0][self.PUBLISHER_ID],
        #                                       pipeline_id=self.vizor,
        #                                       job_id=args[0][self.JOB_ID]).first()

        # if ps is not None:
        #     ps.end_time = end_date
        #     ps.duration_seconds = (end_date - ps.start_time).total_seconds()
        #     ps.status = self.PL_ERROR
        #     ps.error_details = str(exc)
        #     ps.updated = end_date
        #     ps.update()

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
