import codecs
import json
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import Rejected_Articles
from ivetl import utils


@app.task
class GetRejectedArticlesTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        total_count = utils.get_record_count_estimate(publisher_id, product_id, pipeline_id, self.short_name)
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        rejected_articles = Rejected_Articles.objects.filter(publisher_id=publisher_id).fetch_size(1000).limit(1000000)

        target_file_name = work_folder + "/" + publisher_id + "_" + "rejectedarticles" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\tMANUSCRIPT_ID\tDATA\n')

        count = 0

        for article in rejected_articles:

            count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

            # pull out the same subset of fields that are found in the file upload
            data = {
                'manuscript_id': article.manuscript_id,
                'date_of_rejection': article.date_of_rejection.strftime('%m-%d-%Y'),
                'reject_reason': article.reject_reason,
                'title': article.manuscript_title,
                'first_author': article.first_author,
                'corresponding_author': article.corresponding_author,
                'co_authors': article.co_authors,
                'subject_category': article.subject_category,
                'editor': article.editor,
                'submitted_journal': article.submitted_journal,
                'article_type': article.article_type,
                'keywords': article.keywords,
                'custom': article.custom,
                'preprint_doi': article.preprint_doi,
                'source_file_name': article.source_file_name,
            }

            row = """%s\t%s\t%s\n""" % (
                publisher_id,
                article.manuscript_id,
                json.dumps(data)
            )

            target_file.write(row)

        target_file.close()

        # true up the count
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, count)

        return {
            'count': count,
            'input_file': target_file_name,
        }
