from time import time
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.validators import CustomArticleDataValidator


@app.task
class ValidateArticleDataFiles(Task):

    def run_task(self, publisher_id, product_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']
        validator = CustomArticleDataValidator()

        t0 = time()
        total_count, errors = validator.validate_files(files, publisher_id)
        t1 = time()
        tlogger.info("Rows processed:   %s" % (total_count - 1))
        tlogger.info("Time taken:       " + format(t1 - t0, '.2f') + " seconds / " + format((t1 - t0) / 60, '.2f') + " minutes")

        if errors:
            for error in errors:
                tlogger.error(error)
            raise Exception("Validation errors in files: %s" % files)
        else:
            tlogger.info("No errors found")

        return {'input_files': files}
