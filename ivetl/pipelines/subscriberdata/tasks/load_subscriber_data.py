import csv
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import Subscriber
from ivetl import utils


@app.task
class LoadSubscriberDataTask(Task):
    FILE_PATH = '/iv/hwdw-metadata/subscribers/'

    FIELD_NAMES = [
        'ac_database',
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
        'inst_key',
        'modified_by_dt',
        'dw_syb_server',
        'dw_db',
        'subscr_type',
        'subscr_type_desc',
        'ringgold_id',
        'affiliation',
        'user_type',
    ]

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        all_files = []
        for dir_path in self.FILE_DIRS:
            all_files.append([os.path.join(dir_path, n) for n in os.listdir(dir_path) if not n.startswith('.')])

        total_count = 0
        for file_path in all_files:
            total_count += utils.file_len(file_path)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)
        tlogger.info('Found %s records' % total_count)

        count = 0
        for file_path in all_files:
            with open(file_path, encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t', fieldnames=self.FIELD_NAMES)
                for row in reader:
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    # match publisher id
                    publisher_id = 'foo'

                    Subscriber.objects(
                        publisher_id=publisher_id,
                        membership_no=row['membership_no']
                    ).update(
                        ac_database=row['ac_database'],
                        firstname=row['firstname'],
                        lastname=row['lastname'],
                        inst_name=row['inst_name'],
                        user_phone=row['user_phone'],
                        user_fax=row['user_fax'],
                        user_email=row['user_email'],
                        email_domain_srch=row['email_domain_srch'],
                        user_address=row['user_address'],
                        address_2=row['address_2'],
                        title=row['title'],
                        user_systemname=row['user_systemname'],
                        inst_key=row['inst_key'],
                        modified_by_dt=row['modified_by_dt'],
                        subscr_type=row['subscr_type'],
                        subscr_type_desc=row['subscr_type_desc'],
                        ringgold_id=row['ringgold_id'],
                        affiliation=row['affiliation'],
                        user_type=row['user_type'],
                        expired=row['expired'],
                        num_subscriptions=row['num_subscriptions'],
                        sales_agent=row['sales_agent'],
                        memo=row['memo'],
                        tier=row['tier'],
                        consortium=row['consortium'],
                        start_date=row['start_date'],
                        country=row['country'],
                        region=row['region'],
                        contact=row['contact'],
                        institution_alternate_name=row['institution_alternate_name'],
                        institution_alternate_identifier=row['institution_alternate_identifier'],
                        custom1=row['custom1'],
                        custom2=row['custom2'],
                        custom3=row['custom3'],
                    )

        task_args['count'] = total_count

        return task_args
