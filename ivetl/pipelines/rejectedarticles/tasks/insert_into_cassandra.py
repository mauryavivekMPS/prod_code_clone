import csv
import codecs
import json
from decimal import Decimal
from datetime import datetime
import cassandra.util
from cassandra.cqlengine.query import BatchQuery
from ivetl.celery import app
from ivetl.models import Publisher_Vizor_Updates, RejectedArticles
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

                authors_match_score = data.get('author_match_score')
                if authors_match_score:
                    authors_match_score = Decimal(authors_match_score)

                crossref_match_score = data.get('xref_score')
                if crossref_match_score:
                    crossref_match_score = Decimal(crossref_match_score)

                date_of_publication = data.get('xref_publishdate')
                if date_of_publication:
                    date_of_publication = to_datetime(date_of_publication)

                date_of_rejection = data.get('date_of_rejection')
                if date_of_rejection:
                    date_of_rejection = to_datetime(date_of_rejection)

                RejectedArticles.objects(
                    publisher_id=publisher_id,
                    manuscript_id=manuscript_id
                ).update(
                    rejected_article_id=cassandra.util.uuid_from_time(updated),
                    article_type=data.get('article_type'),
                    authors_match_score=authors_match_score,
                    citation_lookup_status=data.get('citation_lookup_status'),
                    co_authors=data.get('co_authors'),
                    corresponding_author=data.get('corresponding_author'),
                    crossref_doi=data.get('xref_doi'),
                    crossref_match_score=crossref_match_score,
                    custom=data.get('custom'),
                    date_of_publication=date_of_publication,
                    date_of_rejection=date_of_rejection,
                    editor=data.get('editor'),
                    first_author=data.get('first_author'),
                    keywords=data.get('keywords'),
                    manuscript_title=data.get('title'),
                    published_co_authors=data.get('xref_co_authors_ln_fn'),
                    published_first_author=data.get('xref_first_author'),
                    published_journal=data.get('xref_journal'),
                    published_journal_issn=data.get('xref_journal_issn'),
                    published_publisher=data.get('xref_published_publisher'),
                    published_title=data.get('xref_title'),
                    reject_reason=data.get('reject_reason'),
                    scopus_doi_status=data.get('scopus_doi_status'),
                    scopus_id=data.get('scopus_id'),
                    source_file_name=data.get('source_file_name'),
                    status=data.get('status'),
                    subject_category=data.get('subject_category'),
                    submitted_journal=data.get('submitted_journal'),
                    preprint_doi=data.get('preprint_doi'),
                    mendeley_saves=int(data.get('mendeley_saves', 0)),
                    citations=int(data.get('citations', 0)),
                    updated=updated,
                    created=updated,
                )

                tlogger.info("Inserting or updating record")

            pu = Publisher_Vizor_Updates()
            pu['publisher_id'] = publisher_id
            pu['vizor_id'] = 'rejected_articles'
            pu['updated'] = updated
            pu.save()

        return {
            'count': count,
        }


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

