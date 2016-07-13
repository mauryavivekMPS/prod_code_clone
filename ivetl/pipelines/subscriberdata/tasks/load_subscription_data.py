import csv
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import Subscription
from ivetl import utils


@app.task
class LoadSubscriptionDataTask(Task):
    FILE_PATHS = [
        '/iv/hwdw-metadata/instadmin.tsv',
        '/iv/hwdw-metadata/individual_subscriptions.tsv',
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
        total_count = 0
        for file_path in self.FILE_PATHS:
            total_count += utils.file_len(file_path)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)
        tlogger.info('Found %s records' % total_count)

        count = 0
        for file_path in self.FILE_PATHS:
            with open(file_path, encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t', fieldnames=self.FIELD_NAMES)
                for row in reader:
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    # match publisher id
                    publisher_id = 'foo'

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
