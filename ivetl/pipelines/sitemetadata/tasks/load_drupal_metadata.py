from dateutil.parser import parse
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.connectors import SmartConnector
from ivetl.models import DrupalMetadata


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
                        launch_date = None

                        if site_id:

                            if 'instances' in site:
                                instances = site['instances']
                                key_1 = site_key + '_production'
                                key_2 = 'production_' + site_key

                                site_record = None
                                if key_1 in instances:
                                    site_record = instances[key_1]
                                elif key_2 in instances:
                                    site_record = instances[key_2]
                                elif len(list(instances.values())):
                                    site_record = list(instances.values())[0]

                                if site_record:
                                    pre_production_site = site_record.get('pre_production')

                                    launch_date_str = site_record.get('site_instance_launch_date')
                                    if launch_date_str:
                                        try:
                                            launch_date = parse(launch_date_str)
                                        except ValueError:
                                            pass

                                    if 'production_url' in site_record:
                                        site_url = site_record.get('production_url')
                                    else:
                                        site_url = site_record.get('primary_url')
                                else:
                                    site_url = ""
                                    pre_production_site = 1
                                    tlogger.info("\n No site_url found for " + site_id)

                                if pre_production_site == 1:
                                    tlogger.info("\n Preproduction Site, skipping: " + site_id)
                                    continue

                            count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                            DrupalMetadata.objects(
                                site_id=site_id
                            ).update(
                                site_code=site_id,
                                name=site_url,
                                publisher=site['publisher_info'].get('title') if 'publisher_info' in site else '',
                                site_url=site_url,
                                umbrella_code=site.get('corpus'),
                                product=site.get('product'),
                                type=site.get('type'),
                                created=str(site.get('created')),
                                launch_date=launch_date,
                            )

        task_args['count'] = count
        return task_args
