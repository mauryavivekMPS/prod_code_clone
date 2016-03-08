import os
import datetime
import stat
import json
from ivetl.common import common
from ivetl.pipelines.base_task import BaseTask
from ivetl.models import Pipeline_Status, Pipeline_Task_Status


class Pipeline(BaseTask):
    abstract = True

    @staticmethod
    def get_or_create_incoming_dir_for_publisher(base_incoming_dir, publisher_id, pipeline_id):
        pipeline_incoming_dir = os.path.join(base_incoming_dir, publisher_id, pipeline_id)
        os.makedirs(pipeline_incoming_dir, exist_ok=True)
        os.chmod(pipeline_incoming_dir, stat.S_IXOTH | stat.S_IROTH | stat.S_IXGRP| stat.S_IRGRP | stat.S_IWGRP | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        return pipeline_incoming_dir

    @staticmethod
    def get_incoming_dir_for_publisher(base_incoming_dir, publisher_id, pipeline_id):
        pipeline_incoming_dir = os.path.join(base_incoming_dir, publisher_id, pipeline_id)
        return pipeline_incoming_dir

    def on_pipeline_started(self, publisher_id, product_id, pipeline_id, job_id, work_folder, params={}, initiating_user_email=None, total_task_count=0, current_task_count=0):
        start_date = datetime.datetime.today()

        Pipeline_Status.objects(
            publisher_id=publisher_id,
            product_id=product_id,
            pipeline_id=pipeline_id,
            job_id=job_id,
        ).update(
            start_time=start_date,
            workfolder=work_folder,
            updated=start_date,
            total_task_count=total_task_count,
            current_task_count=current_task_count,
            user_email=initiating_user_email,
            params_json=json.dumps(params),
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        end_date = datetime.datetime.today()

        # sometimes a pipeline will fail before there are a full set of task args
        publisher_id = ''
        pipeline_id = ''
        product_id = ''
        job_id = ''
        if args and type(args[0]) == dict:
            task_args = args[0]
            publisher_id = task_args.get('publisher_id', '')
            product_id = task_args.get('product_id', '')
            pipeline_id = task_args.get('pipeline_id', '')
            job_id = task_args.get('job_id', '')

            # TODO: Not sure what to do here if there are no args yet!?!

            Pipeline_Task_Status.objects(
                publisher_id=publisher_id,
                product_id=product_id,
                pipeline_id=self.pipeline_name,
                job_id=job_id,
                task_id=self.short_name,
            ).update(
                end_time=end_date,
                status=self.PL_ERROR,
                error_details=str(exc),
                updated=end_date
            )

            try:
                Pipeline_Status.objects(
                    publisher_id=publisher_id,
                    product_id=product_id,
                    pipeline_id=pipeline_id,
                    job_id=job_id,
                ).update(
                    end_time=end_date,
                    duration_seconds=(end_date - ps.start_time).total_seconds(),
                    status=self.PL_ERROR,
                    error_details=str(exc),
                    updated=end_date,
                )
            except Pipeline_Status.DoesNotExist:
                # do nothing
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
        pipeline_id = ''
        if args and type(args[0]) == dict:
            task_args = args[0]
            pipeline_id = task_args.get('pipeline_id', '')

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

    def generate_job_id(self):
        now = datetime.datetime.now()
        today_label = now.strftime('%Y%m%d')
        job_id = now.strftime('%Y%m%d_%H%M%S%f')
        return now, today_label, job_id
