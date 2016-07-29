import os
import csv
import datetime
from dateutil.parser import parse
from collections import defaultdict
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import Subscription, Subscriber, PublisherMetadata
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
            total_count += utils.file_len(file_path, encoding='ISO-8859-2')
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)
        tlogger.info('Found %s records' % total_count)

        # create a publisher lookup
        publisher_id_by_ac_database = {}
        for publisher in PublisherMetadata.objects.all():
            for ac_database in publisher.ac_databases:
                publisher_id_by_ac_database[ac_database] = publisher.publisher_id

        now = datetime.datetime.now()

        expiration_dates_for_member = defaultdict(lambda: defaultdict(list))
        subscriptions_for_member = defaultdict(lambda: defaultdict(int))

        def reader_without_nulls(f):
            while True:
                yield next(f).replace('\0', '')
                continue
            return

        count = 0
        for file_path in all_files:
            with open(file_path, encoding='ISO-8859-2') as subscription_file:
                reader = csv.DictReader(reader_without_nulls(subscription_file), delimiter='\t', fieldnames=self.FIELD_NAMES, quoting=csv.QUOTE_NONE)
                for row in reader:
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    subscription_publisher_id = publisher_id_by_ac_database.get(row['ac_database'])
                    membership_no = row['membership_no']
                    expiration_date = parse(row['expiration_dt'])

                    if subscription_publisher_id:
                        Subscription.objects(
                            publisher_id=subscription_publisher_id,
                            membership_no=membership_no,
                            journal_code=row['journal_code'],
                            subscr_type_cd=row['subscr_type_cd']
                        ).update(
                            institution_number=row['institution_number'],
                            ac_database=row['ac_database'],
                            expiration_dt=expiration_date,
                            subscr_status=row['subscr_status'],
                            last_used_dt=parse(row['last_used_dt']),
                            modified_by_dt=parse(row['modified_by_dt']),
                            product_cd=row['product_cd'],
                            subscr_type=row['subscr_type'],
                            subscr_type_desc=row['subscr_type_desc'],
                        )

                    expiration_dates_for_member[subscription_publisher_id][membership_no].append(expiration_date)
                    subscriptions_for_member[subscription_publisher_id][membership_no] += 1

        for subscription_publisher_id in expiration_dates_for_member:
            for membership_no in expiration_dates_for_member[subscription_publisher_id]:

                try:
                    subscriber = Subscriber.objects.get(
                        publisher_id=subscription_publisher_id,
                        membership_no=membership_no
                    )
                    expired = True
                    for expiration_date in expiration_dates_for_member[subscription_publisher_id][membership_no]:
                        if expiration_date > now:
                            expired = False

                    subscriber.expired = expired
                    subscriber.num_subscriptions = subscriptions_for_member[subscription_publisher_id][membership_no]
                    subscriber.save()

                except Subscriber.DoesNotExist:
                    pass

        task_args['count'] = total_count

        return task_args
