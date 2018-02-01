import os
import json
import datetime
import stat
import uuid
from celery import chain
from ivetl.common import common
from ivetl.pipelines.base_task import BaseTask
from ivetl.models import PipelineStatus, PipelineTaskStatus


class Pipeline(BaseTask):
    abstract = True

    @staticmethod
    def get_or_create_incoming_dir_for_publisher(base_incoming_dir, publisher_id, pipeline_id):
        pipeline_incoming_dir = os.path.join(base_incoming_dir, publisher_id, pipeline_id)
        os.makedirs(pipeline_incoming_dir, exist_ok=True)
        os.chmod(pipeline_incoming_dir, 0o775)
        return pipeline_incoming_dir

    @staticmethod
    def get_incoming_dir_for_publisher(base_incoming_dir, publisher_id, pipeline_id):
        pipeline_incoming_dir = os.path.join(base_incoming_dir, publisher_id, pipeline_id)
        return pipeline_incoming_dir

    def on_pipeline_started(self, publisher_id, product_id, pipeline_id, job_id, work_folder, params={}, initiating_user_email=None, current_task_count=0):
        pipeline = common.PIPELINE_BY_ID[pipeline_id]
        total_task_count = len(pipeline['tasks'])
        start_date = datetime.datetime.today()
        params_json = self.params_to_json(params)

        PipelineStatus.objects(
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
            params_json=params_json,
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        end_date = datetime.datetime.today()

        # sometimes a pipeline will fail before there are a full set of task args
        pipeline_id = ''
        if args and type(args[0]) == dict:
            task_args = args[0]
            publisher_id = task_args.get('publisher_id', '')
            product_id = task_args.get('product_id', '')
            pipeline_id = task_args.get('pipeline_id', '')
            job_id = task_args.get('job_id', '')

            # TODO: Not sure what to do here if there are no args yet!?!

            PipelineTaskStatus.objects(
                publisher_id=publisher_id,
                product_id=product_id,
                pipeline_id=self.pipeline_name,
                job_id=job_id,
                task_id=self.short_name,
            ).update(
                end_time=end_date,
                status=self.PIPELINE_STATUS_ERROR,
                error_details=str(exc),
                updated=end_date
            )

            try:
                ps = PipelineStatus.objects(
                    publisher_id=publisher_id,
                    product_id=product_id,
                    pipeline_id=pipeline_id,
                    job_id=job_id,
                )
                ps.update(
                    end_time=end_date,
                    duration_seconds=(end_date - ps.start_time).total_seconds(),
                    status=self.PIPELINE_STATUS_ERROR,
                    error_details=str(exc),
                    updated=end_date,
                )
            except PipelineStatus.DoesNotExist:
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
        job_id = '%s_%s' % (now.strftime('%Y%m%d_%H%M%S%f'), str(uuid.uuid4()).split('-')[0])
        return now, today_label, job_id

    @staticmethod
    def restart_job(publisher_id, product_id, pipeline_id, job_id, start_from_stopped_task=False):
        pipeline = common.PIPELINE_BY_ID[pipeline_id]

        # reset some of the status properties
        p = PipelineStatus.objects.get(
            publisher_id=publisher_id,
            product_id=product_id,
            pipeline_id=pipeline_id,
            job_id=job_id
        )

        p.update(
            status='in-progress',
            stop_instruction=None,
            end_time=None,
            updated=datetime.datetime.now(),
        )

        if start_from_stopped_task:
            task_status = PipelineTaskStatus.objects.get(
                publisher_id=publisher_id,
                product_id=product_id,
                pipeline_id=pipeline_id,
                job_id=job_id,
                task_id=p.current_task,
            )
            task_to_start_at = p.current_task

        else:
            first_task_id = common.task_id_from_path(pipeline['tasks'][0])
            task_status = PipelineTaskStatus.objects.get(
                publisher_id=publisher_id,
                product_id=product_id,
                pipeline_id=pipeline_id,
                job_id=job_id,
                task_id=first_task_id,
            )
            task_to_start_at = first_task_id

        # parse the task args
        task_args = json.loads(task_status.task_args_json)

        # delete task status records after the chosen task
        found_start_at_task = False
        for task_class_path in pipeline['tasks']:
            task_id = common.task_id_from_path(task_class_path)
            if task_id == task_to_start_at:
                found_start_at_task = True
                continue
            if found_start_at_task:
                try:
                    PipelineTaskStatus.objects.get(
                        publisher_id=publisher_id,
                        product_id=product_id,
                        pipeline_id=pipeline_id,
                        job_id=job_id,
                        task_id=task_id,
                    ).delete()
                except PipelineTaskStatus.DoesNotExist:
                    pass

        # and run the entire pipeline
        Pipeline.chain_tasks(pipeline_id, task_args, start_at=task_to_start_at)

    @staticmethod
    def chain_tasks(pipeline_id, task_args, start_at=None):
        pipeline = common.PIPELINE_BY_ID[pipeline_id]

        if start_at:
            remaining_tasks = []
            found_start_at_task = False
            for task_class_path in pipeline['tasks']:
                task_id = common.task_id_from_path(task_class_path)
                if task_id == start_at:
                    found_start_at_task = True
                if found_start_at_task:
                    remaining_tasks.append(task_class_path)
        else:
            remaining_tasks = pipeline['tasks']

        tasks = []
        first_task = True
        for task_class_path in remaining_tasks:
            task_class = common.get_task_class(task_class_path)

            if first_task:
                tasks.append(task_class.s(task_args))
                first_task = False
            else:
                tasks.append(task_class.s())

        chain(*tasks).delay()
