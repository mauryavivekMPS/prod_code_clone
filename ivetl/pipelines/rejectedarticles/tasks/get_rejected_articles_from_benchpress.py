import re
import os
import shutil
import datetime
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import PublisherJournal
from ivetl.common import common
from ivetl import utils

@app.task
class GetRejectedArticlesFromBenchPressTask(Task):
    BUCKET = common.BENCHPRESS_BUCKET

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        from_date = self.from_json_date(task_args.get('from_date'))
        to_date = self.from_json_date(task_args.get('to_date'))

        today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)

        if from_date:
            from_date = datetime.datetime.combine(from_date, datetime.time.min)

        if to_date:
            to_date = datetime.datetime.combine(to_date, datetime.time.min)

        def _previous_quarter(ref):
            if ref.month < 4:
                return datetime.datetime(ref.year - 1, 10, 1), datetime.datetime(ref.year - 1, 12, 31)
            elif ref.month < 7:
                return datetime.datetime(ref.year, 1, 1), datetime.datetime(ref.year, 3, 31)
            elif ref.month < 10:
                return datetime.datetime(ref.year, 4, 1), datetime.datetime(ref.year, 6, 30)
            else:
                return datetime.datetime(ref.year, 7, 1), datetime.datetime(ref.year, 9, 30)

        if not (from_date or to_date):
            from_date, to_date = _previous_quarter(today)

        if from_date > today - datetime.timedelta(1):
            tlogger.error('Invalid date range: The from date must be before yesterday.')
            raise Exception

        if not to_date:
            to_date = today - datetime.timedelta(1)

        if to_date < from_date:
            tlogger.error('Invalid date range: The date range must be at least one day.')
            raise Exception

        tlogger.info('Using date range: %s to %s' % (from_date.strftime('%Y-%m-%d'), to_date.strftime('%Y-%m-%d')))
        from_strf = from_date.strftime('%m_%d_%Y')
        to_strf = to_date.strftime('%m_%d_%Y')

        journals_with_benchpress = [p.journal_code for p in PublisherJournal.objects.filter(
            publisher_id=publisher_id,
            product_id='published_articles',
            use_benchpress=True
        )]

        total_count = len(journals_with_benchpress)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        files = []
        count = 0

        if journals_with_benchpress:
            for journal_code in journals_with_benchpress:
                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                tlogger.info('Looking for file for journal: %s' % journal_code)

                if pipeline_id == 'benchpress_published_article_data':
                    j_file_name = '%s_foam_%s_%s.txt' % (journal_code,
                    from_strf, to_strf)
                else:
                    j_file_name = '%s_%s_%s.txt' % (journal_code, from_strf,
                    to_strf)
                tlogger.info('Using filename: %s' % j_file_name)

                try:
                    dl_file_path = utils.download_file_from_s3(self.BUCKET, j_file_name)
                    tlogger.info('Retrieved file: %s' % dl_file_path)
                    local_file_path = os.path.join(work_folder, j_file_name)
                except Exception as e:
                    tlogger.info('Failed to retrieve file: %s' % j_file_name)
                    tlogger.info(e)
                    continue

                with open(local_file_path,
                'wb') as local_file, open(dl_file_path,
                'rb') as dl_file:
                    shutil.copyfileobj(dl_file, local_file)

                files.append(local_file_path)
        tlogger.info('Downloaded s3 Files: %s' % ', '.join(files))
        task_args['count'] = count
        task_args['input_files'] = files
        return task_args
