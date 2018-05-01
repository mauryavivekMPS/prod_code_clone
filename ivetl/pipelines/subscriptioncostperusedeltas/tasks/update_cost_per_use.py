import decimal
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import InstitutionUsageStatComposite, InstitutionUsageJournal, SubscriptionCostPerUseByBundleStat, SubscriptionCostPerUseBySubscriberStat, SystemGlobal
from ivetl import utils


@app.task
class UpdateCostPerUseTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        from_date = self.from_json_date(task_args.get('from_date'))
        to_date = self.from_json_date(task_args.get('to_date'))

        categories = {
            'Full-text HTML Requests': 'html_usage',
            'Full-text PDF Requests': 'pdf_usage',
        }

        total_count = utils.get_record_count_estimate(publisher_id, product_id, pipeline_id, self.short_name)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0

        stopped = False

        all_journals = InstitutionUsageJournal.objects.filter(publisher_id=publisher_id, counter_type='jr3')

        for current_month in utils.month_range(from_date, to_date):

            tlogger.info('Processing month %s' % current_month.strftime('%Y-%m'))

            # keep track of the subscriber+bundle elements that we've already seen this month
            seen_subscriber_bundles = set()

            for journal in all_journals:

                tlogger.info('Processing journal %s' % journal)

                # select all html usage for the current (iterated) month
                current_month_usage = InstitutionUsageStatComposite.objects.filter(
                    publisher_id=publisher_id,
                    counter_type='jr3',
                    journal=journal.journal,
                    usage_date=current_month,
                ).fetch_size(1000).limit(10000000)

                # first, fill out cpu by bundle
                for usage in current_month_usage:

                    # early stop support
                    if count % 1000:
                        if self.is_stopped(publisher_id, product_id, pipeline_id, job_id):
                            self.mark_as_stopped(publisher_id, product_id, pipeline_id, job_id)
                            stopped = True
                            break

                    if usage.usage_category in categories and usage.bundle_name:
                        try:
                            s = SubscriptionCostPerUseByBundleStat.objects.get(
                                publisher_id=publisher_id,
                                membership_no=usage.subscriber_id,
                                bundle_name=usage.bundle_name,
                                usage_date=current_month,
                            )
                        except SubscriptionCostPerUseByBundleStat.DoesNotExist:
                            s = SubscriptionCostPerUseByBundleStat.objects.create(
                                publisher_id=publisher_id,
                                membership_no=usage.subscriber_id,
                                bundle_name=usage.bundle_name,
                                usage_date=current_month,
                                amount=usage.amount / 12,
                            )

                        # clear out the usage value if this is the first stat for this month/journal for this sub, add if not
                        if (usage.subscriber_id, usage.bundle_name, usage.usage_category) in seen_subscriber_bundles:
                            s.category_usage[categories[usage.usage_category]] += usage.usage
                        else:
                            s.category_usage[categories[usage.usage_category]] = usage.usage
                            seen_subscriber_bundles.add((usage.subscriber_id, usage.bundle_name, usage.usage_category))

                        total_usage = 0
                        for category_usage in s.category_usage.values():
                            total_usage += category_usage

                        s.total_usage = total_usage

                        if s.amount is not None and total_usage:
                            s.cost_per_use = s.amount / total_usage

                        s.save()

            # second, iterate over the just-created bundle stats
            current_month_bundle_stats = SubscriptionCostPerUseByBundleStat.objects.filter(
                publisher_id=publisher_id,
                usage_date=current_month,
            )

            if stopped:
                break

            for bundle_stat in current_month_bundle_stats:

                # early stop support
                if count % 1000:
                    if self.is_stopped(publisher_id, product_id, pipeline_id, job_id):
                        self.mark_as_stopped(publisher_id, product_id, pipeline_id, job_id)
                        stopped = True
                        break

                try:
                    s = SubscriptionCostPerUseBySubscriberStat.objects.get(
                        publisher_id=publisher_id,
                        membership_no=bundle_stat.membership_no,
                        usage_date=current_month,
                    )
                except SubscriptionCostPerUseBySubscriberStat.DoesNotExist:
                    s = SubscriptionCostPerUseBySubscriberStat.objects.create(
                        publisher_id=publisher_id,
                        membership_no=bundle_stat.membership_no,
                        usage_date=current_month,
                    )

                s.bundle_amount[bundle_stat.bundle_name] = bundle_stat.amount
                s.bundle_usage[bundle_stat.bundle_name] = bundle_stat.total_usage

                total_amount = decimal.Decimal(0.0)
                for bundle_amount in s.bundle_amount.values():
                    if bundle_amount:
                        total_amount += bundle_amount

                total_usage = 0
                for bundle_usage in s.bundle_usage.values():
                    if bundle_usage:
                        total_usage += bundle_usage

                s.total_amount = total_amount
                s.total_usage = total_usage

                if total_amount is not None and total_usage:
                    s.cost_per_use = total_amount / total_usage

                s.save()

                if stopped:
                    break

        task_args['count'] = count
        return task_args
