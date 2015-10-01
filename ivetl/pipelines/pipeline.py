import os
import datetime
from ivetl.common import common
from ivetl.pipelines.base_task import BaseTask
from ivetl.models import Pipeline_Status, Pipeline_Task_Status


class Pipeline(BaseTask):
    abstract = True
    pipeline_name = ''

    @classmethod
    def get_incoming_dir_for_publisher(cls, base_incoming_dir, publisher_id):
        return os.path.join(base_incoming_dir, publisher_id, cls.pipeline_name)

    def on_pipeline_started(self, publisher_id, job_id, work_folder):
        start_date = datetime.datetime.today()

        p = Pipeline_Status()
        p.publisher_id = publisher_id
        p.pipeline_id = self.pipeline_name
        p.job_id = job_id
        p.start_time = start_date
        p.workfolder = work_folder
        p.updated = start_date
        p.save()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        end_date = datetime.datetime.today()

        # sometimes a pipeline will fail before there are a full set of task args
        publisher_id = ''
        job_id = ''
        if args and type(args[0]) == dict:
            task_args = args[0]
            publisher_id = task_args.get('publisher_id', '')
            job_id = task_args.get('job_id', '')

        print('args = %s' % args)

        pts = Pipeline_Task_Status()
        pts.publisher_id = publisher_id
        pts.pipeline_id = self.pipeline_name
        pts.job_id = job_id
        pts.task_id = self.short_name
        pts.end_time = end_date
        pts.status = self.PL_ERROR
        pts.error_details = str(exc)
        pts.updated = end_date
        pts.update()

        print('%s, %s, %s' % (publisher_id, self.pipeline_name, job_id))

        try:
            ps = Pipeline_Status.objects.get(publisher_id=publisher_id, pipeline_id=self.pipeline_name, job_id=job_id)
            ps.update(
                end_time=end_date,
                duration_seconds=(end_date - ps.start_time).total_seconds(),
                status=self.PL_ERROR,
                error_details=str(exc),
                updated=end_date
            )
        except Pipeline_Status.DoesNotExist:
            # do nothing
            pass

        day = end_date.strftime('%Y.%m.%d')
        subject = "ERROR! " + day + " - " + self.pipeline_name + " - " + self.short_name

        body = "<b>Pipeline:</b> <br>"
        body += self.pipeline_name
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
        day = datetime.datetime.today().strftime('%Y.%m.%d')
        subject = "SUCCESS: " + day + " - " + self.pipeline_name + " - " + self.short_name
        body = "<b>Pipeline:</b> <br>"
        body += self.pipeline_name
        body += "<br><br><b>Task:</b> <br>"
        body += self.short_name
        body += "<br><br><b>Arguments:</b> <br>"
        body += str(args)
        body += "<br><br><b>Return Value:</b> <br>"
        body += str(retval)
        common.send_email(subject, body)
