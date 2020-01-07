import codecs
import os
import re

from datetime import datetime
from ivetl.common import common
from ivetl.celery import app
from ivetl.models import ArticleUsage
from ivetl.models import PublishedArticle
from ivetl.pipelines.task import Task


@app.task
class InsertArticleUsageIntoCassandra(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']
        total_count = task_args['count']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        modified_articles_file_name = os.path.join(work_folder, '%s_modifiedarticles.tab' % publisher_id)  # is pub_id redundant?
        modified_articles_file = codecs.open(modified_articles_file_name, 'w', 'utf-8')
        modified_articles_file.write('PUBLISHER_ID\tDOI\n')  # ..and here? we're already in a pub folder

        all_dois = set()

        count = 0

        field_separators = '\s*\t\s*|\s*,\s*'
        
        for f in files:
            with open(f, encoding='utf-8') as tsv_file:
                # Using re.split() instead of csv.DictReader() for flexibility with field delimiters
                header = tsv_file.readline().strip()
                fieldnames = [fn.lower().replace(' ','') for fn in re.split(field_separators, header)]

                pub_dates = {}

                for row in tsv_file:
                    columns = re.split(field_separators, row.strip())
                    line = dict(zip(fieldnames, columns))
                    
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    doi = common.normalizedDoi(line['articledoi'])

                    if pub_dates.get(doi) is None:
                        try:
                            pub_dates[doi] = PublishedArticle.objects.get(publisher_id=publisher_id,
                                                                          article_doi=doi
                                                                         ).date_of_publication
                        except PublishedArticle.DoesNotExist:
                            continue

                    usage_start_date = pub_dates[doi]
                    usage_type = line['type']
                    usage_month = datetime.strptime(str(line['usagemonth'])[:6], '%Y%m')
                    usage_count = int(line['usagecount']) if line['usagecount'] else 0

                    month_number = ( 12 * (usage_month.year - usage_start_date.year)
                                    + usage_month.month - usage_start_date.month
                                    + 1 )

                    # validate the month_number is between date_of_publication and now().month
                    if usage_month > datetime.now() or month_number < 0:
                        continue
                
                    ArticleUsage.objects(
                        publisher_id=publisher_id,                        
                        article_doi=doi,
                        usage_type=usage_type,
                        month_number=month_number,
                    ).update(
                        month_usage=usage_count,
                        usage_start_date=usage_start_date,
                    )

                    all_dois.add(doi)

        # add a record of modified files for next task
        for doi in all_dois:
            modified_articles_file.write("%s\t%s\n" % (publisher_id, doi))

        modified_articles_file.close()

        task_args['count'] = count
        task_args['input_file'] = modified_articles_file_name
        return task_args

