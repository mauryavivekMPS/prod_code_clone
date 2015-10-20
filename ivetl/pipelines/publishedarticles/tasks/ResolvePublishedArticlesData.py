import csv
import datetime
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import Published_Article, Published_Article_Values


@app.task
class ResolvePublishedArticlesData(Task):

    def run_task(self, publisher_id, job_id, work_folder, tlogger, task_args):
        file_name = task_args['modified_articles_file']
        now = datetime.datetime.now()
        with open(file_name, encoding='utf-8') as tsv:
            count = 0
            for line in csv.reader(tsv, delimiter='\t'):
                count += 1

                # skip header row
                if count == 1:
                    continue

                doi = line[1]
                tlogger.info("Processing #%s : %s" % (count - 1, doi))

                # grab the canonical article record that we're operating on
                try:
                    article = Published_Article.objects.get(publisher_id=publisher_id, article_doi=doi)
                    tlogger.info("DOI does not exist in published_article table")
                except Published_Article.DoesNotExist:
                    continue

                # resolve policy: if a value from source=custom is present it always wins
                for field in ['article_type', 'subject_category', 'editor', 'custom', 'custom_2', 'custom_3']:
                    new_value = None
                    try:
                        v = Published_Article_Values.objects.get(article_doi=doi, publisher_id=publisher_id, source='custom', name=field)
                        new_value = v.value_text
                    except Published_Article_Values.DoesNotExist:
                        pass

                    if not new_value:
                        try:
                            v = Published_Article_Values.objects.get(article_doi=doi, publisher_id=publisher_id, source='pa', name=field)
                            new_value = v.value_text
                        except Published_Article_Values.DoesNotExist:
                            pass

                    # update the canonical if there is any non Null/None value (note that "None" is a value)
                    if new_value:
                        setattr(article, field, new_value)

                article.updated = now
                article.save()

            tsv.close()

        self.pipeline_ended(publisher_id, job_id)
        return {self.COUNT: count}
