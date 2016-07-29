from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.models import PublisherMetadata, PublisherJournal


@app.task
class GetRejectedArticlesFromBenchPressPipeline(Pipeline):

    def run(self, publisher_id_list=[], product_id=None, job_id=None, initiating_user_email=None, from_date=None, to_date=None):
        pipeline_id = "benchpress_rejected_articles"

        now, today_label, job_id = self.generate_job_id()

        if publisher_id_list:
            publishers = PublisherMetadata.objects.filter(publisher_id__in=publisher_id_list)
        else:
            # default to production pubs with benchpress support
            publishers = []
            for publisher in PublisherMetadata.objects.filter(demo=False):
                benchpress_journals = PublisherJournal.objects.filter(
                    publisher_id=publisher.publisher_id,
                    product_id='published_articles',
                    use_benchpress=True
                )
                if benchpress_journals.count():
                    publishers.append(publisher)

        publishers = [p for p in publishers if product_id in p.supported_products]

        for publisher in publishers:

            # create work folder, signal the start of the pipeline
            work_folder = self.get_work_folder(today_label, publisher.publisher_id, product_id, pipeline_id, job_id)
            self.on_pipeline_started(publisher.publisher_id, product_id, pipeline_id, job_id, work_folder, initiating_user_email=initiating_user_email)

            # construct the first task args with all of the standard bits + the list of files
            task_args = {
                'pipeline_id': pipeline_id,
                'publisher_id': publisher.publisher_id,
                'product_id': product_id,
                'work_folder': work_folder,
                'job_id': job_id,
                'from_date': from_date,
                'to_date': to_date,
            }

            self.chain_tasks(pipeline_id, task_args)
