import os
import datetime
import csv
import sys
import shutil
from time import time
from ivetl.common import common
from ivetl.pipelines.base_task import BaseTask
from ivetl.models import Pipeline_Status, Pipeline_Task_Status, PublisherMetadata


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
        self.on_task_started(publisher_id, product_id, pipeline_id, job_id, task_work_folder, current_task_count, task_args, tlogger)
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

    def on_task_started(self, publisher_id, product_id, pipeline_id, job_id, work_folder, current_task_count, task_args, tlogger):
        start_date = datetime.datetime.today()

        task_args_json = self.params_to_json(task_args)

        Pipeline_Task_Status.objects(
            publisher_id=publisher_id,
            product_id=product_id,
            pipeline_id=pipeline_id,
            job_id=job_id,
            task_id=self.short_name,
        ).update(
            start_time=start_date,
            total_record_count=0,
            current_record_count=0,
            status=self.PIPELINE_STATUS_IN_PROGRESS,
            updated=start_date,
            workfolder=work_folder,
            task_args_json=task_args_json,
        )

        Pipeline_Status.objects(
            publisher_id=publisher_id,
            product_id=product_id,
            pipeline_id=pipeline_id,
            job_id=job_id
        ).update(
            current_task=self.short_name,
            current_task_count=current_task_count,
            status=self.PIPELINE_STATUS_IN_PROGRESS,
            updated=start_date,
        )

        tlogger.info("Task %s started for publisher %s on %s" % (self.short_name, publisher_id, start_date))

    def on_task_ended(self, publisher_id, product_id, pipeline_id, job_id, start_time, tlogger, count=None):
        t1 = time()
        end_date = datetime.datetime.fromtimestamp(t1)
        duration_seconds = t1 - start_time

        Pipeline_Task_Status.objects(
            publisher_id=publisher_id,
            product_id=product_id,
            pipeline_id=pipeline_id,
            job_id=job_id,
            task_id=self.short_name,
        ).update(
            end_time=end_date,
            status=self.PIPELINE_STATUS_COMPLETED,
            updated=end_date,
            duration_seconds=duration_seconds,
        )

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

        today_label = job_id.split('_')[0]
        work_folder = self.get_work_folder(today_label, publisher_id, product_id, pipeline_id, job_id)
        task_work_folder = self.get_task_work_folder(work_folder)
        tlogger = self.get_task_logger(task_work_folder)

        tlogger.error('Exception: %s' % exc)
        tlogger.error('Traceback:\n %s' % einfo.traceback)
        tlogger.error('Type: %s' % type(args))
        tlogger.error('Type: %s' % type(kwargs))
        # tlogger.error('Args:\n %s' % args)

        Pipeline_Task_Status.objects(
            publisher_id=publisher_id,
            product_id=product_id,
            pipeline_id=pipeline_id,
            job_id=job_id,
            task_id=self.short_name,
        ).update(
            end_time=end_date,
            status=self.PIPELINE_STATUS_ERROR,
            error_details=str(exc),
            updated=end_date,
        )

        try:
            ps = Pipeline_Status.objects.get(publisher_id=publisher_id, product_id=product_id, pipeline_id=pipeline_id, job_id=job_id)
            ps.update(
                end_time=end_date,
                duration_seconds=(end_date - ps.start_time).total_seconds(),
                status=self.PIPELINE_STATUS_ERROR,
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
        Pipeline_Task_Status.objects(
            publisher_id=publisher_id,
            product_id=product_id,
            pipeline_id=pipeline_id,
            job_id=job_id,
            task_id=self.short_name
        ).update(
            total_record_count=total_count
        )

    def increment_record_count(self, publisher_id, product_id, pipeline_id, job_id, total_count, current_count):
        current_count += 1

        if total_count:

            # figure out a reasonable increment
            if total_count <= 100:
                increment = 1
            elif total_count <= 100000:
                increment = 100
            else:
                increment = 1000

        if total_count and current_count % increment == 0:
            # write out every 100 records to the db
            Pipeline_Task_Status.objects(
                publisher_id=publisher_id,
                product_id=product_id,
                pipeline_id=pipeline_id,
                job_id=job_id,
                task_id=self.short_name
            ).update(
                current_record_count=current_count
            )
        return current_count

    def run_validation_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args, validator=None):
        files = task_args['input_files']

        # note: removed temporarily because this is being used with multiple encodings (the JR's in particular)

        # just count the lines
        total_count = 0
        # for file in files:
        #     with open(file) as f:
        #         for i, l in enumerate(f):
        #             pass
        #         total_count = i + 1

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        def increment_count(count):
            return self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

        publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)

        t0 = time()
        total_count, errors = validator.validate_files(
            files,
            issns=publisher.all_issns,
            crossref_username=publisher.crossref_username,
            crossref_password=publisher.crossref_password,
            increment_count_func=increment_count
        )

        t1 = time()
        tlogger.info("Rows processed:   %s" % (total_count - 1))
        tlogger.info("Time taken:       " + format(t1 - t0, '.2f') + " seconds / " + format((t1 - t0) / 60, '.2f') + " minutes")

        if errors:
            for error in errors:
                tlogger.error(error)
            raise Exception("Validation errors in files: %s" % files)
        else:
            tlogger.info("No errors found")

        return {
            'input_files': files,
            'count': total_count,
        }

    def run_get_files_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        preserve_incoming_files = task_args.get('preserve_incoming_files', False)

        total_count = len(task_args['uploaded_files'])
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0

        files = []
        for source_file in task_args['uploaded_files']:

            count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

            # move (or copy) files from incoming to current task folder
            if preserve_incoming_files:
                shutil.copy(source_file, work_folder)
            else:
                shutil.move(source_file, work_folder)

            # compile a list of files for the next task
            files.append(os.path.join(work_folder, os.path.basename(source_file)))

        return {
            'input_files': files,
            'count': count,
        }
