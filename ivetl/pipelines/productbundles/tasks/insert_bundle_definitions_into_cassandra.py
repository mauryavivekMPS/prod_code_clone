import csv
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import ProductBundle


@app.task
class InsertBundleDefinitionsIntoCassandraTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']
        total_count = task_args['count']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0
        for file in files:

            tlogger.info('Processing %s' % file)

            with open(file, 'r', encoding='utf-8') as tsv:
                for line in csv.reader(tsv, delimiter="\t"):

                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    publisher_id = line[0]
                    bundle_name = line[1]

                    issns = []
                    for issn in line[2:]:
                        if issn:
                            issns.append(issn)

                    ProductBundle.objects(
                        publisher_id=publisher_id,
                        bundle_name=bundle_name,
                    ).update(
                        journal_issns=issns,
                    )

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id)

        return {
            'count': count
        }
