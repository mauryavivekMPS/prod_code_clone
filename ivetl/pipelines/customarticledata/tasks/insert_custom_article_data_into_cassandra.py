import os
import csv
import codecs
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import PublishedArticleValues
from ivetl.pipelines.customarticledata import CustomArticleDataPipeline


@app.task
class InsertCustomArticleDataIntoCassandra(Task):

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
                for line in csv.reader(tsv, delimiter='\t'):
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    # skip header row
                    if count == 1:
                        continue

                    d = {
                        'doi': line[0].strip(),
                        'article_type': line[1].strip().title(),
                        'subject_category': line[2].strip().title(),
                        'editor': line[3].strip(),
                        'custom': line[4].strip(),
                        'custom_2': line[5].strip(),
                        'custom_3': line[6].strip()
                    }

                    doi = d['doi'].lower().strip()
                    tlogger.info("Processing #%s : %s" % (count - 1, doi))

                    for field in CustomArticleDataPipeline.FOAM_FIELDS:

                        new_value = d[field]

                        # skip if there is no value, this is a no-op
                        if not new_value:
                            continue

                        # if there is any version of a "none" string, then standardize it
                        if new_value.lower() == 'none':
                            new_value = 'None'

                        PublishedArticleValues.objects(article_doi=doi, publisher_id=publisher_id, source='custom', name=field).update(value_text=new_value)

                    # add a record of modified files for next task
                    modified_articles_file.write("%s\t%s\n" % (publisher_id, doi))

        modified_articles_file.close()

        task_args['count'] = total_count
        task_args['input_file'] = modified_articles_file_name

        return task_args
