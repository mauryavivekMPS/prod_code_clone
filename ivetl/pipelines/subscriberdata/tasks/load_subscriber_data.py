import os
import csv
import time
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import Subscriber, PublisherMetadata, SubscriberValues
from ivetl.pipelines.subscriberdata import SubscribersAndSubscriptionsPipeline
from ivetl import utils


@app.task
class LoadSubscriberDataTask(Task):
    FILE_DIRS = [
        '/iv/hwdw-metadata/subscribers/',
    ]

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
        total_t0 = time.time()
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

        overlapping_fields_in_file = set(SubscribersAndSubscriptionsPipeline.OVERLAPPING_FIELDS).intersection(set(self.FIELD_NAMES))

        def reader_without_nulls(f):
            while True:
                yield next(f).replace('\0', '')
                continue
            return

        count = 0
        for file_path in all_files:
            with open(file_path, encoding='ISO-8859-2') as subscriber_file:
                reader = csv.DictReader(reader_without_nulls(subscriber_file), delimiter='\t', fieldnames=self.FIELD_NAMES, quoting=csv.QUOTE_NONE)
                for row in reader:
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    subscriber_publisher_id = publisher_id_by_ac_database.get(row['ac_database'])
                    membership_no = row['membership_no']
                    if subscriber_publisher_id:
                        sub_update_t0 = time.time()
                        Subscriber.objects(
                            publisher_id=subscriber_publisher_id,
                            membership_no=membership_no,
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
                        )
                        sub_update_t1 = time.time()

                        field_update_t0 = time.time()
                        for field in overlapping_fields_in_file:
                            SubscriberValues.objects(
                                publisher_id=subscriber_publisher_id,
                                membership_no=membership_no,
                                source='hw',
                                name=field,
                            ).update(
                                value_text=row[field],
                            )
                        field_update_t1 = time.time()

                        if not count % 1000:
                            print('query times: %f %f' % (sub_update_t1 - sub_update_t0, field_update_t1 - field_update_t0))

        task_args['count'] = total_count

        total_t1 = time.time()
        print('total task time: %f' % (total_t1 - total_t0))

        return task_args
