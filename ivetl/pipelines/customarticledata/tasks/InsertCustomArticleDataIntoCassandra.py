import os
import csv
import codecs
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.pipelines.customarticledata import utils
from ivetl.models import Published_Article_Values


@app.task
class InsertCustomArticleDataIntoCassandra(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']

        modified_articles_file_name = os.path.join(work_folder, '%s_modifiedarticles.tab' % publisher_id)  # is pub_id redundant?
        modified_articles_file = codecs.open(modified_articles_file_name, 'w', 'utf-8')
        modified_articles_file.write('PUBLISHER_ID\tDOI\n')  # ..and here? we're already in a pub folder

        for f in files:
            with open(f, encoding='utf-8') as tsv:
                count = 0
                for line in csv.reader(tsv, delimiter='\t'):
                    count += 1

                    # skip header row
                    if count == 1:
                        continue

                    d = utils.parse_custom_data_line(line)

                    doi = d['doi'].lower().strip()
                    tlogger.info("Processing #%s : %s" % (count - 1, doi))

                    # data is added only to the values table and we let the resolver figure out the rest
                    Published_Article_Values.objects(article_doi=doi, publisher_id=publisher_id, source='custom', name='article_type').update(value_text=d['toc_section'])
                    Published_Article_Values.objects(article_doi=doi, publisher_id=publisher_id, source='custom', name='subject_category').update(value_text=d['collection'])
                    Published_Article_Values.objects(article_doi=doi, publisher_id=publisher_id, source='custom', name='editor').update(value_text=d['editor'])
                    Published_Article_Values.objects(article_doi=doi, publisher_id=publisher_id, source='custom', name='custom').update(value_text=d['custom'])
                    Published_Article_Values.objects(article_doi=doi, publisher_id=publisher_id, source='custom', name='custom_2').update(value_text=d['custom_2'])
                    Published_Article_Values.objects(article_doi=doi, publisher_id=publisher_id, source='custom', name='custom_3').update(value_text=d['custom_3'])

                    # add a record of modified files for next task
                    modified_articles_file.write("%s\t%s\n" % (publisher_id, doi))
                    modified_articles_file.flush()  # why is this needed?

                tsv.close()

        modified_articles_file.close()
        return {self.COUNT: count, 'modified_articles_file': modified_articles_file_name}
