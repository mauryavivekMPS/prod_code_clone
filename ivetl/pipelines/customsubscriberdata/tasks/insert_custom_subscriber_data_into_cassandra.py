import os
import csv
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import SubscriberValues


@app.task
class InsertCustomSubscriberDataIntoCassandraTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']
        total_count = task_args['count']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        modified_articles_file_name = os.path.join(work_folder, '%s_modifiedarticles.tab' % publisher_id)  # is pub_id redundant?
        modified_articles_file = open(modified_articles_file_name, 'w', encoding='utf-8')
        modified_articles_file.write('PUBLISHER_ID\tDOI\n')  # ..and here? we're already in a pub folder

        # TODO: update all of this with the right details!!

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
                        'toc_section': line[1].strip().title(),
                        'collection': line[2].strip().title(),
                        'editor': line[3].strip(),
                        'custom': line[4].strip(),
                        'custom_2': line[5].strip(),
                        'custom_3': line[6].strip()
                    }

                    doi = d['doi'].lower().strip()
                    tlogger.info("Processing #%s : %s" % (count - 1, doi))

                    # data is added only to the values table and we let the resolver figure out the rest
                    SubscriberValues.objects(article_doi=doi, publisher_id=publisher_id, source='custom', name='article_type').update(value_text=d['toc_section'])
                    SubscriberValues.objects(article_doi=doi, publisher_id=publisher_id, source='custom', name='subject_category').update(value_text=d['collection'])
                    SubscriberValues.objects(article_doi=doi, publisher_id=publisher_id, source='custom', name='editor').update(value_text=d['editor'])
                    SubscriberValues.objects(article_doi=doi, publisher_id=publisher_id, source='custom', name='custom').update(value_text=d['custom'])
                    SubscriberValues.objects(article_doi=doi, publisher_id=publisher_id, source='custom', name='custom_2').update(value_text=d['custom_2'])
                    SubscriberValues.objects(article_doi=doi, publisher_id=publisher_id, source='custom', name='custom_3').update(value_text=d['custom_3'])

                    # add a record of modified files for next task
                    modified_articles_file.write("%s\t%s\n" % (publisher_id, doi))
                    modified_articles_file.flush()  # why is this needed?

        modified_articles_file.close()

        task_args['count'] = total_count
        task_args['input_file'] = modified_articles_file_name

        return task_args
