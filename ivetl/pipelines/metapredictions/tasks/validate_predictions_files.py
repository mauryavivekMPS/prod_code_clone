from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.validators import MetaPredictionsValidator


@app.task
class ValidatePredictionsFilesTask(Task):
    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        return self.run_validation_task(
            publisher_id,
            product_id,
            pipeline_id,
            job_id,
            work_folder,
            tlogger,
            task_args,
            validator=MetaPredictionsValidator()
        )
