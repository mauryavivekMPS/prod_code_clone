import csv
import datetime
from dateutil.parser import parse
from collections import defaultdict
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import Subscription, Subscriber, PublisherMetadata
from ivetl import utils
from ivetl.common import common


@app.task
class LoadSubscriptionDataTask(Task):
    S3_DIRS = [
        'instadmin/',
        # 'individual_subscriptions/',
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
        for s3_dir in self.S3_DIRS:
            new_files = utils.download_files_from_s3_dir(common.HWDW_METADATA_BUCKET, s3_dir)
            all_files.extend(new_files)

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

        subscription_details_for_member = defaultdict(lambda: defaultdict(list))
        subscriptions_for_member = defaultdict(lambda: defaultdict(int))

        def reader_without_nulls(f):
            while True:
                yield next(f).replace('\0', '')
                continue
            return

        count = 0
        for file_path in all_files:
            with open(file_path, encoding='ISO-8859-2') as subscription_file:
                tlogger.info('Processing file %s' % file_path)
                reader = csv.DictReader(reader_without_nulls(subscription_file), delimiter='\t', fieldnames=self.FIELD_NAMES, quoting=csv.QUOTE_NONE)
                for row in reader:
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    if not count % 100000:
                        tlogger.info('Completed %s rows' % count)

                    subscription_publisher_id = publisher_id_by_ac_database.get(row['ac_database'])
                    membership_no = row.get('membership_no')
                    journal_code = row.get('journal_code')
                    subscriber_type_code = row.get('subscr_type_cd')
                    subscr_status = row.get('subscr_status')

                    if not subscription_publisher_id:
                        tlogger.info('No publisher ID for line %s, skipping...' % count)
                        continue

                    if not membership_no:
                        tlogger.info('No membership no on line %s, skipping...' % count)
                        continue

                    if not journal_code:
                        tlogger.info('No journal_code on line %s, skipping...' % count)
                        continue

                    if not subscriber_type_code:
                        tlogger.info('No subscriber_type_code on line %s, skipping...' % count)
                        continue

                    if not subscr_status:
                        tlogger.info('No subscr_status on line %s, skipping...' % count)
                        continue

                    expiration_date_str = row['expiration_dt']
                    if not expiration_date_str:
                        tlogger.info('No expiration date on line %s, skipping...' % count)
                        continue

                    try:
                        expiration_date = parse(expiration_date_str)
                    except ValueError:
                        tlogger.info('Invalid expiration date on line %s, skipping...' % count)
                        continue

                    last_used_date_str = row['last_used_dt']
                    if not last_used_date_str:
                        tlogger.info('No last used date on line %s, skipping...' % count)
                        continue

                    try:
                        last_used_date = parse(last_used_date_str)
                    except ValueError:
                        tlogger.info('Invalid last used date on line %s, skipping...' % count)
                        continue

                    modified_by_date_str = row['modified_by_dt']
                    if not modified_by_date_str:
                        tlogger.info('No modified by date on line %s, skipping...' % count)
                        continue

                    try:
                        modified_by_date = parse(modified_by_date_str)
                    except ValueError:
                        tlogger.info('Invalid modified by date on line %s, skipping...' % count)
                        continue

                    Subscription.objects(
                        publisher_id=subscription_publisher_id,
                        membership_no=membership_no,
                        journal_code=journal_code,
                        subscr_type_cd=subscriber_type_code
                    ).update(
                        institution_number=row['institution_number'],
                        ac_database=row['ac_database'],
                        expiration_dt=expiration_date,
                        subscr_status=subscr_status,
                        last_used_dt=last_used_date,
                        modified_by_dt=modified_by_date,
                        product_cd=row['product_cd'],
                        subscr_type=row['subscr_type'],
                        subscr_type_desc=row['subscr_type_desc'],
                    )

                    subscription_details_for_member[subscription_publisher_id][membership_no].append({
                        'expiration_date': expiration_date,
                        'subscr_status': subscr_status,
                    })

                    subscriptions_for_member[subscription_publisher_id][membership_no] += 1

        for subscription_publisher_id in subscription_details_for_member:
            for membership_no in subscription_details_for_member[subscription_publisher_id]:

                try:
                    subscriber = Subscriber.objects.get(
                        publisher_id=subscription_publisher_id,
                        membership_no=membership_no
                    )

                    # assume all subs for this member expired and look for single counter example
                    expired = True
                    final_expiration_date = None
                    for subscription_details in subscription_details_for_member[subscription_publisher_id][membership_no]:
                        if subscription_details['expiration_date'] > now and subscription_details['subscr_status'] != 'HOLD':
                            expired = False
                        if not final_expiration_date or subscription_details['expiration_date'] > final_expiration_date:
                            final_expiration_date = subscription_details['expiration_date']
                    subscriber.expired = expired
                    subscriber.final_expiration_date = final_expiration_date
                    subscriber.num_subscriptions = subscriptions_for_member[subscription_publisher_id][membership_no]
                    subscriber.save()

                except Subscriber.DoesNotExist:
                    pass

        task_args['count'] = total_count

        return task_args
