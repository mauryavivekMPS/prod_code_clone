from time import time
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.validators import CustomArticleDataValidator


@app.task
class ValidateArticleDataFiles(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']
        validator = CustomArticleDataValidator()

        # just count the lines
        total_count = 0
        for file in files:
            with open(file) as f:
                for i, l in enumerate(f):
                    pass
                total_count = i + 1

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        def increment_count(count):
            return self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

        t0 = time()
        total_count, errors = validator.validate_files(files, publisher_id, increment_count)
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
