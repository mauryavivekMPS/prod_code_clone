import os
import csv
import codecs
from datetime import datetime
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import ArticleUsage
from ivetl.models import PublishedArticle


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

        # Warning: this CQL query has a LIMIT 10000
        publisher_dois = PublishedArticle.objects(publisher_id=publisher_id)

        for f in files:
            with open(f, encoding='utf-8') as tsv:
                for line in csv.DictReader(tsv, delimiter='\t'):

                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    doi = line['Article DOI'].lower()

                    try:
                        article = publisher_dois.get(article_doi=doi)
                    except PublishedArticle.DoesNotExist:
                        break
                    
                    usage_start_date = article.date_of_publication
                    usage_type = line['Type']

                    usage_string = line['Usage Count']
                    if usage_string:
                        usage = int(usage_string)
                    else:
                        usage = 0

                    usage_month = datetime.strptime(line['Usage Month'], '%Y%m')
                    
                    month_number = ( 12 * (usage_month.year - usage_start_date.year)
                                    + usage.month - usage_start_date.month
                                    + 1 )
                                   
                    ArticleUsage.objects(
                        publisher_id=publisher_id,                        
                        article_doi=doi,
                        usage_type=usage_type,
                        month_number=month_number,
                    ).update(
                        month_usage=usage,
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

