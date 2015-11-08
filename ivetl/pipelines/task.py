import datetime
from time import time
import csv
import sys
from ivetl.common import common
from ivetl.pipelines.base_task import BaseTask
from ivetl.models import Pipeline_Status, Pipeline_Task_Status


class Task(BaseTask):
    abstract = True

    def run(self, task_args):
        new_task_args = task_args.copy()

        # pull the standard args out of task args
        publisher_id = new_task_args.pop('publisher_id')
        product_id = new_task_args.pop('product_id')
        work_folder = new_task_args.pop('work_folder')
        job_id = new_task_args.pop('job_id')
        pipeline_id = new_task_args.pop('pipeline_id')

        if 'current_task_count' in new_task_args:
            current_task_count = new_task_args.pop('current_task_count')
        else:
            current_task_count = 0

        # bump the task count
        current_task_count += 1

        # set up the directory for this task
        task_work_folder, tlogger = self.setup_task(work_folder)
        csv.field_size_limit(sys.maxsize)

        # run the task
        t0 = time()
        self.on_task_started(publisher_id, product_id, pipeline_id, job_id, task_work_folder, current_task_count, tlogger)
        task_result = self.run_task(publisher_id, product_id, pipeline_id, job_id, task_work_folder, tlogger, new_task_args)
        self.on_task_ended(publisher_id, product_id, pipeline_id, job_id, t0, tlogger, task_result.get('count'))

        # construct a new task args with the result
        task_result['publisher_id'] = publisher_id
        task_result['product_id'] = product_id
        task_result['work_folder'] = work_folder
        task_result['job_id'] = job_id
        task_result['pipeline_id'] = pipeline_id
        task_result['current_task_count'] = current_task_count

        return task_result

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        raise NotImplementedError

    def on_task_started(self, publisher_id, product_id, pipeline_id, job_id, work_folder, current_task_count, tlogger):
        start_date = datetime.datetime.today()

        pts = Pipeline_Task_Status()
        pts.publisher_id = publisher_id
        pts.product_id = product_id
        pts.pipeline_id = pipeline_id
        pts.job_id = job_id
        pts.task_id = self.short_name
        pts.start_time = start_date
        pts.total_record_count = 0
        pts.current_record_count = 0
        pts.status = self.PL_INPROGRESS
        pts.updated = start_date
        pts.workfolder = work_folder
        pts.save()

        Pipeline_Status.objects(publisher_id=publisher_id, product_id=product_id, pipeline_id=pipeline_id, job_id=job_id).update(
            current_task=self.short_name,
            current_task_count=current_task_count,
            status=self.PL_INPROGRESS,
            updated=start_date,
        )

        tlogger.info("Task %s started for publisher %s on %s" % (self.short_name, publisher_id, start_date))

    def on_task_ended(self, publisher_id, product_id, pipeline_id, job_id, start_time, tlogger, count=None):
        t1 = time()
        end_date = datetime.datetime.fromtimestamp(t1)
        duration_seconds = t1 - start_time

        pts = Pipeline_Task_Status()
        pts.publisher_id = publisher_id
        pts.product_id = product_id
        pts.pipeline_id = pipeline_id
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
        pipeline_id = task_args['pipeline_id']
        publisher_id = task_args['publisher_id']
        product_id = task_args['product_id']
        job_id = task_args['job_id']

        pts = Pipeline_Task_Status()
        pts.publisher_id = publisher_id
        pts.product_id = product_id
        pts.pipeline_id = pipeline_id
        pts.job_id = job_id
        pts.task_id = self.short_name
        pts.end_time = end_date
        pts.status = self.PL_ERROR
        pts.error_details = str(exc)
        pts.updated = end_date
        pts.update()

        try:
            ps = Pipeline_Status.objects.get(publisher_id=publisher_id, product_id=product_id, pipeline_id=pipeline_id, job_id=job_id)
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
        subject = "ERROR! " + day + " - " + pipeline_id + " - " + self.short_name
        body = "<b>Pipeline:</b> <br>"
        body += pipeline_id
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
        pipeline_id = task_args['pipeline_id']
        day = datetime.datetime.today().strftime('%Y.%m.%d')
        subject = "SUCCESS: " + day + " - " + pipeline_id + " - " + self.short_name
        body = "<b>Pipeline:</b> <br>"
        body += pipeline_id
        body += "<br><br><b>Task:</b> <br>"
        body += self.short_name
        body += "<br><br><b>Arguments:</b> <br>"
        body += str(args)
        body += "<br><br><b>Return Value:</b> <br>"
        body += str(retval)
        common.send_email(subject, body)

    def set_total_record_count(self, publisher_id, product_id, pipeline_id, job_id, total_count):
        Pipeline_Task_Status.objects(publisher_id=publisher_id, product_id=product_id, pipeline_id=pipeline_id, job_id=job_id, task_id=self.short_name).update(
            total_record_count=total_count
        )

    def increment_record_count(self, publisher_id, product_id, pipeline_id, job_id, total_count, current_count):
        current_count += 1

        if total_count:

            # figure out a reasonable increment
            if total_count < 10:
                increment = 1
            else:
                increment = int(total_count / 10)

        if total_count and current_count % increment == 0:
            # write out every 100 records to the db
            Pipeline_Task_Status.objects(publisher_id=publisher_id, product_id=product_id, pipeline_id=pipeline_id, job_id=job_id, task_id=self.short_name).update(
                current_record_count=current_count
            )
        return current_count

    def pipeline_ended(self, publisher_id, product_id, pipeline_id, job_id):
        end_date = datetime.datetime.today()
        p = Pipeline_Status().objects.filter(publisher_id=publisher_id, product_id=product_id, pipeline_id=pipeline_id, job_id=job_id).first()
        if p is not None:
            p.end_time = end_date
            p.duration_seconds = (end_date - p.start_time).total_seconds()
            p.status = self.PL_COMPLETED
            p.updated = end_date
            p.update()
