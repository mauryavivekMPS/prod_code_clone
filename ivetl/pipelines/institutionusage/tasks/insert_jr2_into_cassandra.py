import csv
import datetime
from dateutil.parser import parse
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import InstitutionUsageStat, InstitutionUsageStatComposite, InstitutionUsageJournal


@app.task
class InsertJR2IntoCassandraTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']
        total_count = task_args['count']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        seen_journals = {j.journal for j in InstitutionUsageJournal.objects.filter(publisher_id=publisher_id, counter_type='jr2')}

        count = 0
        for file in files:

            tlogger.info('Processing %s' % file)

            date_cols = []
            num_cols = 6
            with open(file, 'r', encoding='ISO-8859-1') as tsv:
                got_header_for_file = False

                for line in csv.reader(tsv, delimiter="\t"):
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    if not got_header_for_file:

                        # date cols start here
                        col = num_cols

                        # collect all of them (we support any number of them)
                        while line[col] != 'YTD Total':
                            month_date = parse(line[col])
                            full_date = datetime.date(month_date.year, month_date.month, 1)  # hard set to 1st of month
                            date_cols.append((col, full_date))
                            col += 1

                        num_cols += len(date_cols)

                        tlogger.info('Found %s date columns' % len(date_cols))
                        got_header_for_file = True
                        continue

                    if len(line) < num_cols:
                        tlogger.info('Unexpected number of cols, skipping row...')
                        continue

                    subscriber_id = line[0]
                    institution_name = line[1]
                    journal = line[2]
                    journal_print_issn = line[3]
                    journal_online_issn = line[4]
                    usage_category = line[5]

                    if journal not in seen_journals:
                        InstitutionUsageJournal.objects.create(
                            publisher_id=publisher_id,
                            counter_type='jr2',
                            journal=journal,
                        )
                        seen_journals.add(journal)

                    for col, date in date_cols:

                        try:
                            usage = int(line[col])
                        except ValueError:
                            continue

                        InstitutionUsageStat.objects(
                            publisher_id=publisher_id,
                            counter_type='jr2',
                            journal=journal,
                            subscriber_id=subscriber_id,
                            usage_date=date,
                            usage_category=usage_category,
                        ).update(
                            journal_print_issn=journal_print_issn,
                            journal_online_issn=journal_online_issn,
                            institution_name=institution_name,
                            usage=usage,
                        )

                        InstitutionUsageStatComposite.objects(
                            publisher_id=publisher_id,
                            counter_type='jr2',
                            journal=journal,
                            subscriber_id=subscriber_id,
                            usage_date=date,
                            usage_category=usage_category,
                        ).update(
                            journal_print_issn=journal_print_issn,
                            journal_online_issn=journal_online_issn,
                            institution_name=institution_name,
                            usage=usage,
                        )

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, tlogger, show_alerts=task_args['show_alerts'])

        task_args['count'] = count
        return task_args
