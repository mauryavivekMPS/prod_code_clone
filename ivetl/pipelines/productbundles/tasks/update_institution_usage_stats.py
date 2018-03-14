import datetime
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import InstitutionUsageStat, InstitutionUsageStatComposite, SubscriptionPricing, ProductBundle
from ivetl.common import common
from ivetl import utils


@app.task
class UpdateInstitutionUsageStatsTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        from_date = self.from_json_date(task_args['from_date'])

        if not from_date:
            from_date = datetime.datetime(2013, 1, 1)

        now = datetime.datetime.now()
        to_date = datetime.datetime(now.year, now.month, 1)

        cluster = Cluster(common.CASSANDRA_IP_LIST)
        session = cluster.connect()

        count = 0

        for date in utils.month_range(from_date, to_date):

            publisher_stats_sql = """
              select subscriber_id, journal, usage_category, usage_date, journal_print_issn, journal_online_issn
              from impactvizor.institution_usage_stat
              where publisher_id = %s
              and counter_type = %s
              and usage_date = %s
              limit 100000000
            """

            publisher_stats_statement = SimpleStatement(publisher_stats_sql, fetch_size=1000)

            total_count = 100000  # cheap estimate
            self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

            for stat in session.execute(publisher_stats_statement, (publisher_id, 'jr3', date)):
                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                # get subscriptions for this pub and year
                matching_subscriptions = SubscriptionPricing.objects.filter(
                    publisher_id=publisher_id,
                    membership_no=stat.subscriber_id,
                    year=stat.usage_date.year,
                )

                # find one with a matching ISSN
                match = None
                for subscription in matching_subscriptions:
                    try:
                        bundle = ProductBundle.objects.get(
                            publisher_id=publisher_id,
                            bundle_name=subscription.bundle_name,
                        )

                        issns = bundle.journal_issns
                        if stat.journal_print_issn in issns or stat.journal_online_issn in issns:
                            match = subscription
                            break

                    except ProductBundle.DoesNotExist:
                        pass

                if match:
                    InstitutionUsageStat.objects(
                        publisher_id=publisher_id,
                        counter_type='jr3',
                        journal=stat.journal,
                        subscriber_id=stat.subscriber_id,
                        usage_date=stat.usage_date,
                        usage_category=stat.usage_category,
                    ).update(
                        bundle_name=match.bundle_name,
                        trial=match.trial,
                        trial_expiration_date=match.trial_expiration_date,
                        amount=match.amount,
                    )

                    InstitutionUsageStatComposite.objects(
                        publisher_id=publisher_id,
                        counter_type='jr3',
                        journal=stat.journal,
                        subscriber_id=stat.subscriber_id,
                        usage_date=stat.usage_date,
                        usage_category=stat.usage_category,
                    ).update(
                        bundle_name=match.bundle_name,
                        trial=match.trial,
                        trial_expiration_date=match.trial_expiration_date,
                        amount=match.amount,
                    )

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, tlogger, show_alerts=task_args['show_alerts'])

        task_args['count'] = count
        return task_args
