from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.connectors import SmartConnector
from ivetl.models import Drupal_Metadata


@app.task
class LoadDrupalMetadataTask(Task):
    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        smart = SmartConnector(tlogger=tlogger)
        metadata = smart.get_metadata()

        count = 0
        total_count = 1000  # just a guess
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        for cluster_name in metadata['clusters']:
            if 'dev' not in cluster_name:
                if 'sites' in metadata['clusters'][cluster_name]:
                    for site_key in metadata['clusters'][cluster_name]['sites']:

                        site = metadata['clusters'][cluster_name]['sites'][site_key]
                        site_id = site.get('identifier')

                        if site_id:

                            if 'instances' in site:
                                if site_key + '_production' in site['instances']:
                                    pre_production_site = site['instances'][site_key + '_production'].get('pre_production')
                                    if 'production_url' in site['instances'][site_key + '_production']:
                                        site_url = site['instances'][site_key + '_production'].get('production_url')
                                    else:
                                        site_url = site['instances'][site_key + '_production'].get('primary_url')

                                elif 'production_' + site_key in site['instances']:
                                    pre_production_site = site['instances']['production_' + site_key].get('pre_production')
                                    if 'production_url' in site['instances']['production_' + site_key]:
                                        site_url = site['instances']['production_' + site_key].get('production_url')
                                    else:
                                        site_url = site['instances']['production_' + site_key].get('primary_url')

                                elif list(site['instances'].values())[0]:
                                    pre_production_site = list(site['instances'].values())[0].get('pre_production')
                                    if 'production_url' in list(site['instances'].values())[0]:
                                        site_url = list(site['instances'].values())[0].get('production_url')
                                    else:
                                        site_url = list(site['instances'].values())[0].get('primary_url')
                                else:
                                    site_url = ""
                                    pre_production_site = 1
                                    tlogger.info("\n No site_url found for " + site_id)

                                if pre_production_site == 1:
                                    tlogger.info("\n Preproduction Site, skipping: " + site_id)
                                    continue

                            count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                            Drupal_Metadata.objects(
                                site_id=site_id
                            ).update(
                                site_code=site_id,
                                name=site_url,
                                publisher=site['publisher_info'].get('title') if 'publisher_info' in site else '',
                                site_url=site_url,
                                umbrella_code=site.get('corpus'),
                                product=site.get('product'),
                                type=site.get('type'),
                                created=site.get('created'),
                            )

        return {
            'count': count
        }
