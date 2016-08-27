import json
import datetime
from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.models import PublisherMetadata, PublisherJournal, PipelineStatus
from ivetl.common import common


@app.task
class UpdatePublishedArticlesPipeline(Pipeline):
    PUB_START_DATE = datetime.date(2010, 1, 1)
    COHORT_PUB_START_DATE = datetime.date(2013, 1, 1)
    PUB_OVERLAP_MONTHS = 2

    def run(self, publisher_id_list=[], product_id=None, job_id=None, start_at_stopped_task=False, reprocess_all=False, articles_per_page=1000, max_articles_to_process=None, initiating_user_email=None, run_monthly_job=False):
        pipeline_id = "published_articles"

        now, today_label, job_id = self.generate_job_id()

        product = common.PRODUCT_BY_ID[product_id]

        if publisher_id_list:
            publishers = PublisherMetadata.objects.filter(publisher_id__in=publisher_id_list)
        else:
            publishers = PublisherMetadata.objects.filter(demo=False)  # default to production pubs

        publishers = [p for p in publishers if product_id in p.supported_products]

        for pm in publishers:

            publisher_id = pm.publisher_id

            # get ISSNs by product to deal with cohort or not
            issns = [j.print_issn for j in PublisherJournal.objects.filter(publisher_id=publisher_id, product_id=product_id)]
            issns.extend([j.electronic_issn for j in PublisherJournal.objects.filter(publisher_id=publisher_id, product_id=product_id)])

            if product['cohort']:
                start_publication_date = self.COHORT_PUB_START_DATE
            else:
                start_publication_date = self.PUB_START_DATE

            # pipelines are per publisher, so now that we have data, we start the pipeline work
            work_folder = self.get_work_folder(today_label, publisher_id, product_id, pipeline_id, job_id)
            self.on_pipeline_started(publisher_id, product_id, pipeline_id, job_id, work_folder, initiating_user_email=initiating_user_email)

            task_args = {
                'product_id': product_id,
                'publisher_id': publisher_id,
                'pipeline_id': pipeline_id,
                'work_folder': work_folder,
                'job_id': job_id,
                'issns': issns,
                'start_pub_date': self.to_json_date(start_publication_date),
                'articles_per_page': articles_per_page,
                'max_articles_to_process': max_articles_to_process,
                'run_monthly_job': run_monthly_job,
            }

            Pipeline.chain_tasks(pipeline_id, task_args)

    @staticmethod
    def generate_electronic_issn_lookup(publisher_id, product_id):
        """ Create a lookup to allow resolving both ISSNs to the electronic ISSN. """
        journals_for_publisher = PublisherJournal.objects.filter(publisher_id=publisher_id, product_id=product_id)
        electronic_issn_lookup = {j.electronic_issn: j.electronic_issn for j in journals_for_publisher}
        electronic_issn_lookup.update({j.print_issn: j.electronic_issn for j in journals_for_publisher})
        return electronic_issn_lookup
