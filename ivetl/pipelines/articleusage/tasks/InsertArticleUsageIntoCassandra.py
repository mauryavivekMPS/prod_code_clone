import os
import csv
import codecs
from dateutil import parser
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import Article_Usage


@app.task
class InsertArticleUsageIntoCassandra(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']
        total_count = task_args['count']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        modified_articles_file_name = os.path.join(work_folder, '%s_modifiedarticles.tab' % publisher_id)  # is pub_id redundant?
        modified_articles_file = codecs.open(modified_articles_file_name, 'w', 'utf-8')
        modified_articles_file.write('PUBLISHER_ID\tDOI\n')  # ..and here? we're already in a pub folder

        for f in files:
            with open(f, encoding='utf-8') as tsv:
                count = 0

                for line in csv.DictReader(tsv, delimiter='\t'):
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    doi = line['Article DOI'].lower()
                    usage_start_date = parser.parse(line['Pub Date'])
                    usage_type = line['Type']
                    month_number = int(line['Month Number'])

                    usage_string = line['Usage Count']
                    if usage_string:
                        usage = int(usage_string)
                    else:
                        usage = 0

                    Article_Usage.objects(
                        article_doi=doi,
                        publisher_id=publisher_id,
                        usage_type=usage_type,
                        month_number=month_number,
                    ).update(
                        month_usage=usage,
                        usage_start_date=usage_start_date,
                    )

                    # add a record of modified files for next task
                    modified_articles_file.write("%s\t%s\n" % (publisher_id, doi))
                    modified_articles_file.flush()  # why is this needed?

        modified_articles_file.close()
        return {
            'count': count,
            'input_file': modified_articles_file_name,
        }
