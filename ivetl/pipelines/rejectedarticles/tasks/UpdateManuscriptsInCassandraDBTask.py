from __future__ import absolute_import

import csv
import codecs
from time import time
import json
from decimal import Decimal
from datetime import datetime
from os import makedirs


import cassandra.util
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from cassandra.cqlengine import connection
from cassandra.cqlengine.query import BatchQuery


from ivetl.common import common
from ivetl.celery import app
from ivetl.common.BaseTask import BaseTask

# TODO: !! Is this deprecated?? It hasn't been updated and doesn't seem to be referenced anywhere

@app.task
class UpdateManuscriptsInCassandraDBTask(BaseTask):

    taskname = "UpdateManuscriptsInCassandraDB"
    vizor = common.RAT

    def run(self, args):

        file = args[0]
        publisher = args[1]
        day = args[2]
        workfolder = args[3]

        path = workfolder + "/" + self.taskname
        makedirs(path, exist_ok=True)

        tlogger = self.getTaskLogger(path, self.taskname)

        connection.setup([common.CASSANDRA_IP], common.CASSANDRA_KEYSPACE_IV)

        t0 = time()
        count = 0

        with codecs.open(file, encoding="utf-16") as tsv:

            for line in csv.reader(tsv, delimiter="\t"):

                count += 1
                if count == 1:
                    continue

                publisher = line[0]
                manuscript_id = line[1]
                data = json.loads(line[2])

                if publisher == 'aaas' and (data['submitted_journal'] == 'Signaling' or data['submitted_journal'] == 'Translational Medicine'):
                    continue

                updated = datetime.today()

                b = BatchQuery()

                existing_record = Rejected_Articles.objects.filter(publisher_id=publisher, manuscript_id=manuscript_id).first()

                if existing_record:
                    existing_record.batch(b).delete()

                ra = Rejected_Articles()

                ra['publisher_id'] = publisher
                ra['rejected_article_id'] = cassandra.util.uuid_from_time(updated)
                ra['manuscript_id'] = manuscript_id
                ra['updated'] = updated
                ra['created'] = updated

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
                    ra['crossref_doi'] = data['xref_doi']

                if 'xref_score' in data and (data['xref_score'] != ''):
                    ra['crossref_match_score'] = Decimal(data['xref_score'])

                if 'custom' in data and (data['custom'] != ''):
                    ra['custom'] = data['custom']

                if 'xref_publishdate' in data and (data['xref_publishdate'] != ''):
                    ra['date_of_publication'] = toDateTime(data['xref_publishdate'])

                if 'date_of_rejection' in data and (data['date_of_rejection'] != ''):
                    ra['date_of_rejection'] = toDateTime(data['date_of_rejection'])

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

                if 'xref_journal' in data and (data['xref_journal'] != ''):
                    ra['published_journal'] = data['xref_journal']

                if 'xref_journal_issn' in data and (data['xref_journal_issn'] != ''):
                    ra['published_journal_issn'] = data['xref_journal_issn']

                if 'xref_published_publisher' in data and (data['xref_published_publisher'] != ''):
                    ra['published_publisher'] = data['xref_published_publisher']

                if 'xref_title' in data and (data['xref_title'] != ''):
                    ra['published_title'] = data['xref_title']

                if 'reject_reason' in data and (data['reject_reason'] != ''):

                    ra['reject_reason'] = data['reject_reason']

                    if publisher == 'aaas':
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

                ra.batch(b).save()

                b.execute()

                tlogger.info("\n" + str(count-1) + ". Inserting record: " + publisher + " / " + manuscript_id)


            tsv.close()

            pu = Publisher_Vizor_Updates()
            pu['publisher_id'] = publisher
            pu['vizor_id'] = 'rejected_articles'
            pu['updated'] = updated
            pu.save()


        t1 = time()
        tlogger.info("Rows Processed:   " + str(count - 1))
        tlogger.info("Time Taken:       " + format(t1-t0, '.2f') + " seconds / " + format((t1-t0)/60, '.2f') + " minutes")

        return

def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()

def unix_time_millis(dt):
    return (unix_time(dt) * 1000.0)

def toDateTime(mdy_str):
    dor_parts = mdy_str.split('/')
    dor_month = int(dor_parts[0])
    dor_day = int(dor_parts[1])
    dor_year = int(dor_parts[2])

    if dor_year < 99:
        dor_year += 2000

    # date (y, m, d)
    dor_date = datetime(dor_year, dor_month, dor_day)
    return dor_date


class Publisher_Vizor_Updates(Model):

    publisher_id = columns.Text(primary_key=True)
    vizor_id = columns.Text(primary_key=True)
    updated = columns.DateTime()


class Rejected_Articles(Model):

    publisher_id = columns.Text(primary_key=True)
    rejected_article_id = columns.TimeUUID(primary_key=True)
    article_type = columns.Text(required=False)
    authors_match_score = columns.Decimal(required=False)
    citation_lookup_status = columns.Text(required=False)
    citations = columns.Integer(required=False)
    co_authors = columns.Text(required=False)
    corresponding_author = columns.Text(required=False)
    created = columns.DateTime()
    crossref_doi = columns.Text(required=False)
    crossref_match_score = columns.Decimal(required=False)
    custom = columns.Text(required=False)
    date_of_publication = columns.DateTime(required=False)
    date_of_rejection = columns.DateTime()
    editor = columns.Text()
    first_author = columns.Text(required=False)
    keywords = columns.Text(required=False)
    manuscript_id = columns.Text()
    manuscript_title = columns.Text()
    published_co_authors = columns.Text(required=False)
    published_first_author = columns.Text(required=False)
    published_journal = columns.Text(required=False)
    published_journal_issn = columns.Text(required=False)
    published_publisher = columns.Text(required=False)
    published_title = columns.Text(required=False)
    reject_reason = columns.Text()
    scopus_doi_status = columns.Text(required=False)
    scopus_id = columns.Text(required=False)
    source_file_name = columns.Text()
    status = columns.Text()
    subject_category = columns.Text(required=False)
    submitted_journal = columns.Text()
    updated = columns.DateTime()



