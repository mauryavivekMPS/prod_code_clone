__author__ = 'nmehta, johnm'

from celery import Task
import logging
from os import makedirs
from ivetl.common import common


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

    @property
    def short_name(self):
        return self.name[self.name.rfind('.') + 1:]

    def get_work_folder(self, day, publisher, job_id):
        return common.BASE_WORK_DIR + day + "/" + publisher + "/" + self.vizor + "/" + job_id

    def setup_task(self, workfolder):
        task_workfolder = workfolder + "/" + self.short_name
        makedirs(task_workfolder, exist_ok=True)
        tlogger = self.get_task_logger(task_workfolder)
        return task_workfolder, tlogger

    def get_task_logger(self, path):
        ti_logger = logging.getLogger(path)
        fh = logging.FileHandler(path + "/" + self.short_name + ".log", mode='w', encoding='utf-8')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ti_logger.addHandler(fh)
        return ti_logger



