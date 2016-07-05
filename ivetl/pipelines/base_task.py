import os
import logging
from celery import Task
from ivetl.common import common


class BaseTask(Task):
    abstract = True

    PUBLISHER_ID = 'BaseTask.PublisherId'
    INPUT_FILE = 'BaseTask.InputFile'
    WORK_FOLDER = 'BaseTask.WorkFolder'
    JOB_ID = 'BaseTask.JobId'
    COUNT = 'BaseTask.Count'

    PL_STARTED = "started"
    PL_INPROGRESS = "in-progress"
    PL_COMPLETED = "completed"
    PL_ERROR = "error"

    @property
    def short_name(self):
        return self.name[self.name.rfind('.') + 1:]

    def get_work_folder(self, day, publisher_id, product_id, pipeline_id, job_id):
        return os.path.join(common.BASE_WORK_DIR, day, publisher_id, pipeline_id, job_id)

    def get_task_work_folder(self, work_folder):
        return os.path.join(work_folder, self.short_name)

    def setup_task(self, work_folder):
        task_work_folder = self.get_task_work_folder(work_folder)
        os.makedirs(task_work_folder, exist_ok=True)
        tlogger = self.init_task_logger(task_work_folder)
        return task_work_folder, tlogger

    def init_task_logger(self, task_work_folder):
        ti_logger = logging.getLogger(task_work_folder)
        fh = logging.FileHandler(task_work_folder + "/" + self.short_name + ".log", mode='w', encoding='utf-8')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ti_logger.addHandler(fh)
        ti_logger.propagate = False
        return ti_logger

    def get_task_logger(self, task_work_folder):
        return logging.getLogger(task_work_folder)
