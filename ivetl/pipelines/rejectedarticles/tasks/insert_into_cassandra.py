import csv
import codecs
import json
from decimal import Decimal
from datetime import datetime
import cassandra.util
from ivetl.celery import app
from ivetl.models import PublisherVizorUpdates, RejectedArticles
from ivetl.pipelines.task import Task


@app.task
class InsertIntoCassandraDBTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        file = task_args['input_file']
        total_count = task_args['count']

        count = 0
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        updated = datetime.today()

        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):
                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                if count == 1:
                    continue  # ignore the header

                publisher_id = line[0]
                manuscript_id = line[1]
                data = json.loads(line[2])

                tlogger.info("\n" + str(count-1) + " of " + str(total_count) + ". Processing record: " + publisher_id + " / " + manuscript_id)

                # special case skip
                if publisher_id == 'aaas' and (data['submitted_journal'] == 'Signaling' or data['submitted_journal'] == 'Translational Medicine'):
                    continue

                try:
                    r = RejectedArticles.objects.get(publisher_id=publisher_id, manuscript_id=manuscript_id)
                except RejectedArticles.DoesNotExist:
                    r = RejectedArticles(publisher_id=publisher_id, manuscript_id=manuscript_id)
                    r.rejected_article_id = cassandra.util.uuid_from_time(updated)
                    r.created = updated

                article_type = data.get('article_type')
                if article_type != r.article_type:
                    r.article_type = article_type

                citation_lookup_status = data.get('citation_lookup_status')
                if citation_lookup_status:
                    r.citation_lookup_status = citation_lookup_status

                co_authors = data.get('co_authors')
                if co_authors != r.co_authors:
                    r.co_authors = co_authors

                corresponding_author = data.get('corresponding_author')
                if corresponding_author != r.corresponding_author:
                    r.corresponding_author = corresponding_author

                crossref_doi = data.get('xref_doi')
                if crossref_doi:
                    r.crossref_doi = crossref_doi

                custom = data.get('custom')
                if custom != r.custom:
                    r.custom = custom

                custom_2 = data.get('custom_2')
                if custom_2 != r.custom_2:
                    r.custom_2 = custom_2

                custom_3 = data.get('custom_3')
                if custom_3 != r.custom_3:
                    r.custom_3 = custom_3

                editor = data.get('editor')
                if editor != r.editor:
                    r.editor = editor

                first_author = data.get('first_author')
                if first_author != r.first_author:
                    r.first_author = first_author

                keywords = data.get('keywords')
                if keywords != r.keywords:
                    r.keywords = keywords

                manuscript_title = data.get('title')
                if manuscript_title != r.manuscript_title:
                    r.manuscript_title = manuscript_title

                published_co_authors = data.get('xref_co_authors_ln_fn')
                if published_co_authors:
                    r.published_co_authors = published_co_authors

                published_first_author = data.get('xref_first_author')
                if published_first_author:
                    r.published_first_author = published_first_author

                published_journal = data.get('xref_journal')
                if published_journal:
                    r.published_journal = published_journal

                published_journal_issn = data.get('xref_journal_issn')
                if published_journal_issn:
                    r.published_journal_issn = published_journal_issn

                published_publisher = data.get('xref_published_publisher')
                if published_publisher:
                    r.published_publisher = published_publisher

                published_title = data.get('xref_title')
                if published_title:
                    r.published_title = published_title

                reject_reason = data.get('reject_reason')
                if reject_reason != r.reject_reason:
                    r.reject_reason = reject_reason

                scopus_doi_status = data.get('scopus_doi_status')
                if scopus_doi_status:
                    r.scopus_doi_status = scopus_doi_status

                scopus_id = data.get('scopus_id')
                if scopus_id:
                    r.scopus_id = scopus_id

                source_file_name = data.get('source_file_name')
                if source_file_name:
                    r.source_file_name = source_file_name

                status = data.get('status')
                if status:
                    r.status = status

                subject_category = data.get('subject_category')
                if subject_category != r.subject_category:
                    r.subject_category = subject_category

                submitted_journal = data.get('submitted_journal')
                if submitted_journal != r.submitted_journal:
                    r.submitted_journal = submitted_journal

                preprint_doi = data.get('preprint_doi')
                if preprint_doi:
                    r.preprint_doi = preprint_doi

                authors_match_score = data.get('author_match_score')
                if authors_match_score:
                    r.authors_match_score = Decimal(authors_match_score)

                crossref_match_score = data.get('xref_score')
                if crossref_match_score:
                    r.crossref_match_score = Decimal(crossref_match_score)

                date_of_publication = data.get('xref_publishdate')
                if date_of_publication:
                    r.date_of_publication = to_datetime(date_of_publication)

                date_of_rejection = data.get('date_of_rejection')
                if date_of_rejection:
                    r.date_of_rejection = to_datetime(date_of_rejection)

                mendeley_saves = data.get('mendeley_saves')
                if not mendeley_saves:
                    r.mendeley_saves = 0
                else:
                    r.mendeley_saves = int(mendeley_saves)

                citations = data.get('citations')
                if not citations:
                    r.citations = 0
                else:
                    r.citations = int(citations)

                # if the status changed to not published make sure to clear out 'published' fields
                if r.status == 'Not Published' and r.published_journal is not None:
                    r.crossref_doi = None
                    r.crossref_match_score = None
                    r.date_of_publication = None
                    r.published_co_authors = None
                    r.published_first_author = None
                    r.published_journal = None
                    r.published_journal_issn = None
                    r.published_publisher = None
                    r.published_title = None
                    r.scopus_doi_status = None
                    r.scopus_id = None

                r.updated = updated

                r.save()

                tlogger.info("Inserting or updating record")

            pu = PublisherVizorUpdates()
            pu['publisher_id'] = publisher_id
            pu['vizor_id'] = 'rejected_articles'
            pu['updated'] = updated
            pu.save()

        task_args['count'] = count
        return task_args


def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()


def unix_time_millis(dt):
    return unix_time(dt) * 1000.0


def to_datetime(mdy_str):

    if '-' in mdy_str:
        dor_parts = mdy_str.split('-')
    else:
        dor_parts = mdy_str.split('/')

    dor_month = int(dor_parts[0])
    dor_day = int(dor_parts[1])
    dor_year = int(dor_parts[2])

    if dor_year < 99:
        dor_year += 2000

    # date (y, m, d)
    dor_date = datetime(dor_year, dor_month, dor_day)
    return dor_date

