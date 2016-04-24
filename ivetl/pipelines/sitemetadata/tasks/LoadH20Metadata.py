import csv
import os
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import Highwire_Metadata



@app.task
class LoadH20MetadataTask(Task):
    METADATA_FILE = '/iv/hwdw-metadata/journalinfo/hwdw_journal_info.txt'

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        fieldnames = (
            'sort_name',
            'site_id',
            'site_code',
            'name',
            'site_abbr',
            'print_issn',
            'online_issn',
            'publisher',
            'site_url',
            'umbrella_code',
            'umbrella_url',
            'usage_rpts_feature',
            'journal_info_feature',
            'ac_machine',
            'ac_syb_server',
            'ac_db',
            'ac_port',
            'journal_doi',
            'counter_code',
            'dw_syb_server',
            'dw_db',
            'content_db',
            'content_syb_server',
            'subman_url',
            'legacy_type',
            'legacy_date',
            'dw_site_type',
            'is_book',
            'has_athens',
            'sage_subject_area'
        )

        count = 0
        total_count = 1000  # just a guess
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        # Using S3 fuse, need to set permissions on file
        os.system('chmod +r ' + self.METADATA_FILE)

        with open(self.METADATA_FILE) as highwire_metadata_file:
            reader = csv.DictReader(highwire_metadata_file, delimiter='\t', fieldnames=fieldnames)
            for row in reader:
                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                Highwire_Metadata.objects(site_id=row['site_id']).update(
                    sort_name=row['sort_name'],
                    site_code=row['site_code'],
                    name=row['name'],
                    site_abbr=row['site_abbr'],
                    print_issn=row['print_issn'],
                    online_issn=row['online_issn'],
                    publisher=row['publisher'],
                    site_url=row['site_url'],
                    umbrella_code=row['umbrella_code'],
                    umbrella_url=row['umbrella_url'],
                    usage_rpts_feature=row['usage_rpts_feature'],
                    journal_info_feature=row['journal_info_feature'],
                    ac_machine=row['ac_machine'],
                    ac_syb_server=row['ac_syb_server'],
                    ac_db=row['ac_db'],
                    ac_port=row['ac_port'],
                    journal_doi=row['journal_doi'],
                    counter_code=row['counter_code'],
                    dw_syb_server=row['dw_syb_server'],
                    dw_db=row['dw_db'],
                    content_db=row['content_db'],
                    content_syb_server=row['content_syb_server'],
                    subman_url=row['subman_url'],
                    legacy_type=row['legacy_type'],
                    legacy_date=row['legacy_date'],
                    dw_site_type=row['dw_site_type'],
                    is_book=row['is_book'],
                    has_athens=row['has_athens'],
                    sage_subject_area=row['sage_subject_area'],
                )

        return {
            'count': count
        }
