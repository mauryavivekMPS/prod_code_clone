import cassandra.util
import codecs
import csv
import json

from datetime import datetime
from decimal import Decimal
from ivetl.common import common
from ivetl.celery import app
from ivetl.models import RejectedArticles
from ivetl.pipelines.task import Task


@app.task
class UpdateManuscriptsInCassandraTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        file = task_args['input_file']
        total_count = task_args['count']

        count = 0
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                if count == 1:
                    continue  # ignore the header

                publisher = line[0]
                manuscript_id = line[1]
                data = json.loads(line[2])

                if publisher == 'aaas' and (data['submitted_journal'] == 'Signaling' or data['submitted_journal'] == 'Translational Medicine'):
                    continue

                updated = datetime.today()

                try:
                    ra = RejectedArticles.objects.get(publisher_id=publisher_id, manuscript_id=manuscript_id)
                except RejectedArticles.DoesNotExist:
                    ra = RejectedArticles(publisher_id=publisher_id, manuscript_id=manuscript_id)
                    ra.rejected_article_id = cassandra.util.uuid_from_time(updated)
                    ra.created = updated

                ra['updated'] = updated

                if 'article_type' in data and (data['article_type'] != ''):
                    ra['article_type'] = data['article_type']

                if 'author_match_score' in data and (data['author_match_score'] != ''):
                    ra['authors_match_score'] = Decimal(data['author_match_score'])

                if 'citation_lookup_status' in data and (data['citation_lookup_status'] != ''):
                    ra['citation_lookup_status'] = data['citation_lookup_status']

                if 'citations' in data and (data['citations'] != ''):
                    ra['citations'] = int(data['citations'])

                if 'co_authors' in data and (data['co_authors'] != ''):
                    ra['co_authors'] = data['co_authors']

                if 'corresponding_author' in data and (data['corresponding_author'] != ''):
                    ra['corresponding_author'] = data['corresponding_author']

                if 'xref_doi' in data and (data['xref_doi'] != ''):
                    ra['crossref_doi'] = common.normalizedDoi(data['xref_doi'])

                if 'xref_score' in data and (data['xref_score'] != ''):
                    ra['crossref_match_score'] = Decimal(data['xref_score'])

                if 'custom' in data and (data['custom'] != ''):
                    ra['custom'] = data['custom']

                if 'xref_publishdate' in data and (data['xref_publishdate'] != ''):
                    ra['date_of_publication'] = to_datetime(data['xref_publishdate'])

                if 'date_of_rejection' in data and (data['date_of_rejection'] != ''):
                    ra['date_of_rejection'] = to_datetime(data['date_of_rejection'])

                if 'editor' in data and (data['editor'] != ''):
                    ra['editor'] = data['editor']

                if 'first_author' in data and (data['first_author'] != ''):
                    ra['first_author'] = data['first_author']

                if 'keywords' in data and (data['keywords'] != ''):
                    ra['keywords'] = data['keywords']

                if 'title' in data and (data['title'] != ''):
                    ra['manuscript_title'] = data['title']

                if 'xref_co_authors_ln_fn' in data and (data['xref_co_authors_ln_fn'] != ''):
                    ra['published_co_authors'] = data['xref_co_authors_ln_fn']

                if 'xref_first_author' in data and (data['xref_first_author'] != ''):
                    ra['published_first_author'] = data['xref_first_author']

                if 'xref_journal' in data and (data['xref_jsournal'] != ''):
                    ra['published_journal'] = data['xref_journal']

                if 'xref_journal_issn' in data and (data['xref_journal_issn'] != ''):
                    ra['published_journal_issn'] = data['xref_journal_issn']

                if 'xref_published_publisher' in data and (data['xref_published_publisher'] != ''):
                    ra['published_publisher'] = data['xref_published_publisher']

                if 'xref_title' in data and (data['xref_title'] != ''):
                    ra['published_title'] = data['xref_title']

                if 'reject_reason' in data and (data['reject_reason'] != ''):

                    ra['reject_reason'] = data['reject_reason']

                    if publisher_id == 'aaas':
                        if data['reject_reason'] == 'TRUE':
                            ra['reject_reason'] = 'Reviewed'
                        else:
                            ra['reject_reason'] = 'Not Reviewed'

                if 'scopus_doi_status' in data and (data['scopus_doi_status'] != ''):
                    ra['scopus_doi_status'] = data['scopus_doi_status']

                if 'scopus_id' in data and (data['scopus_id'] != ''):
                    ra['scopus_id'] = data['scopus_id']

                if 'source_file_name' in data and (data['source_file_name'] != ''):
                    ra['source_file_name'] = data['source_file_name']

                if 'status' in data and (data['status'] != ''):
                    ra['status'] = data['status']

                if 'subject_category' in data and (data['subject_category'] != ''):
                    ra['subject_category'] = data['subject_category']

                if 'submitted_journal' in data and (data['submitted_journal'] != ''):
                    ra['submitted_journal'] = data['submitted_journal']

                ra.save()

                tlogger.info("\n" + str(count-1) + ". Inserting/updating record: " + publisher + " / " + manuscript_id)

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, tlogger, show_alerts=task_args['show_alerts'])

        task_args['count'] = count
        return task_args


def to_datetime(mdy_str):
    dor_parts = mdy_str.split('/')
    dor_month = int(dor_parts[0])
    dor_day = int(dor_parts[1])
    dor_year = int(dor_parts[2])

    if dor_year < 99:
        dor_year += 2000

    # date (y, m, d)
    dor_date = datetime(dor_year, dor_month, dor_day)
    return dor_date
