from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.connectors import CrossrefConnector


@app.task
class GetCrossrefArticleCitationsTask(Task):

    def run_task(self, publisher_id, job_id, work_folder, tlogger, task_args):
        crossref = CrossrefConnector()
        return {self.INPUT_FILE: task_args[self.INPUT_FILE], self.COUNT: task_args[self.COUNT]}
