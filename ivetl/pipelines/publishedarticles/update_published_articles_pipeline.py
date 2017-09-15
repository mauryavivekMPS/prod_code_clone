import json
from dateutil.parser import parse
from ivetl.celery import app
from ivetl.pipelines.pipeline import Pipeline
from ivetl.models import PublisherMetadata, PublisherJournal, PipelineStatus


@app.task
class UpdatePublishedArticlesPipeline(Pipeline):
    PUB_OVERLAP_MONTHS = 2

    def run(self, publisher_id_list=[], product_id=None, job_id=None, from_date=None, start_at_stopped_task=False, reprocess_all=False, articles_per_page=1000, max_articles_to_process=None, initiating_user_email=None, run_monthly_job=False, send_alerts=False):
        pipeline_id = "published_articles"

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

            params = {}
            today_label = ''

            if job_id:
                try:
                    ps = PipelineStatus.objects.get(
                        publisher_id=publisher_id,
                        product_id=product_id,
                        pipeline_id=pipeline_id,
                        job_id=job_id,
                    )

                    today_label = job_id.split("_")[0]

                    if ps.params_json:
                        params = json.loads(ps.params_json)

                        if params['from_date']:
                            from_date = parse(params['from_date'])

                except PipelineStatus.DoesNotExist:
                    pass

            if not job_id:
                now, today_label, job_id = self.generate_job_id()

                params = {
                    'from_date': from_date.strftime('%Y-%m-%d') if from_date else None,
                }

            # pipelines are per publisher, so now that we have data, we start the pipeline work
            work_folder = self.get_work_folder(today_label, publisher_id, product_id, pipeline_id, job_id)
            self.on_pipeline_started(publisher_id, product_id, pipeline_id, job_id, work_folder, initiating_user_email=initiating_user_email, params=params)

            task_args = {
                'product_id': product_id,
                'publisher_id': publisher_id,
                'pipeline_id': pipeline_id,
                'work_folder': work_folder,
                'job_id': job_id,
                'from_date': self.to_json_date(from_date),
                'issns': issns,
                'articles_per_page': articles_per_page,
                'max_articles_to_process': max_articles_to_process,
                'run_monthly_job': run_monthly_job,
                'send_alerts': send_alerts,
            }

            Pipeline.chain_tasks(pipeline_id, task_args)

    @staticmethod
    def generate_electronic_issn_lookup(publisher_id, product_id):
        """ Create a lookup to allow resolving both ISSNs to the electronic ISSN. """
        journals_for_publisher = PublisherJournal.objects.filter(publisher_id=publisher_id, product_id=product_id)
        electronic_issn_lookup = {j.electronic_issn: j.electronic_issn for j in journals_for_publisher}
        electronic_issn_lookup.update({j.print_issn: j.electronic_issn for j in journals_for_publisher})
        return electronic_issn_lookup
