__author__ = 'johnm'

import csv
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.pipelines.customarticledata import utils
from ivetl.models import Published_Article, Published_Article_Values


@app.task
class InsertCustomArticleDataIntoCassandra(Task):
    pipeline_name = "custom_article_data"

    def run_task(self, publisher_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']

        for f in files:
            with open(f) as tsv:  # TODO: perhaps should be codecs.open(f, encoding="utf-16") ??
                count = 0
                for line in csv.reader(tsv, delimiter='\t'):
                    count += 1

                    # skip header row
                    if count == 1:
                        continue

                    d = utils.parse_custom_data_line(line)

                    doi = d['doi']

                    # first add/update the values table
                    Published_Article_Values.objects(article_doi=doi, publisher_id=publisher_id, source='custom', name='article_type').update(value_text=d['toc_section'])
                    Published_Article_Values.objects(article_doi=doi, publisher_id=publisher_id, source='custom', name='collection').update(value_text=d['subject_category'])
                    Published_Article_Values.objects(article_doi=doi, publisher_id=publisher_id, source='custom', name='editor').update(value_text=d['editor'])
                    Published_Article_Values.objects(article_doi=doi, publisher_id=publisher_id, source='custom', name='custom').update(value_text=d['custom'])

                    article = Published_Article.get(publisher_id=publisher_id, article_doi=d['doi'])

                tsv.close()

        self.pipeline_ended(publisher_id, self.pipeline_name, job_id)

        return {'input_files': files}
