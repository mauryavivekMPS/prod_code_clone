import os
import csv
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import Subscription, PublisherMetadata
from ivetl import utils


@app.task
class LoadSubscriptionDataTask(Task):
    FILE_DIRS = [
        '/iv/hwdw-metadata/instadmin/',
        '/iv/hwdw-metadata/individual_subscriptions/',
    ]

    FIELD_NAMES = [
        'institution_number',
        'ac_database',
        'subscr_type_cd',
        'journal_code',
        'firstname',
        'first_srch',
        'lastname',
        'last_srch',
        'inst_name',
        'inst_srch',
        'user_phone',
        'user_fax',
        'user_email',
        'email_srch',
        'email_domain_srch',
        'user_address',
        'address_2',
        'title',
        'user_id',
        'membership_no',
        'user_systemname',
        'expiration_dt',
        'subscr_status',
        'last_used_dt',
        'inst_key',
        'modified_by_dt',
        'dw_syb_server',
        'counter_code',
        'dw_db',
        'product_cd',
        'subscr_type',
        'subscr_type_desc',
        'ringgold_id',
        'affiliation',
    ]

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        all_files = []
        for dir_path in self.FILE_DIRS:
            all_files.extend([os.path.join(dir_path, n) for n in os.listdir(dir_path) if not n.startswith('.')])

        total_count = 0
        for file_path in all_files:
            total_count += utils.file_len(file_path, encoding='windows-1252')
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)
        tlogger.info('Found %s records' % total_count)

        # create a publisher lookup
        publisher_id_by_ac_database = {}
        for publisher in PublisherMetadata.objects.all():
            for ac_database in publisher.ac_databases:
                publisher_id_by_ac_database[ac_database] = publisher.publisher_id

        count = 0
        for file_path in all_files:
            with open(file_path, encoding='windows-1252') as f:
                reader = csv.DictReader(f, delimiter='\t', fieldnames=self.FIELD_NAMES)
                for row in reader:
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    publisher_id = publisher_id_by_ac_database.get(row['ac_database'])
                    if publisher_id:
                        Subscription.objects(
                            publisher_id=publisher_id,
                            membership_no=row['membership_no'],
                            journal_code=row['journal_code'],
                            subscr_type_cd=row['subscr_type_cd']
                        ).update(
                            institution_number=row['institution_number'],
                            ac_database=row['ac_database'],
                            expiration_dt=row['expiration_dt'],
                            subscr_status=row['subscr_status'],
                            last_used_dt=row['last_used_dt'],
                            modified_by_dt=row['modified_by_dt'],
                            product_cd=row['product_cd'],
                            subscr_type=row['subscr_type'],
                            subscr_type_desc=row['subscr_type_desc'],
                        )

        task_args['count'] = total_count

        return task_args
