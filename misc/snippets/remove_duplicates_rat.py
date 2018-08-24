#!/usr/bin/env python

import os
os.sys.path.append(os.environ['IVETL_ROOT'])

import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl.celery import open_cassandra_connection, close_cassandra_connection


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
    manuscript_id = columns.Text(index=True)
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
    submitted_journal = columns.Text(index=True)
    mendeley_saves = columns.Integer(required=False)
    preprint_doi = columns.Text(required=False)
    updated = columns.DateTime()

class Publisher_Metadata(Model):
    publisher_id = columns.Text(primary_key=True)
    name = columns.Text()
    email = columns.Text()
    hw_addl_metadata_available = columns.Boolean()
    issn_to_hw_journal_code = columns.Map(columns.Text(), columns.Text())
    published_articles_issns_to_lookup = columns.List(columns.Text())
    published_articles_last_updated = columns.DateTime()
    scopus_api_keys = columns.List(columns.Text())
    crossref_username = columns.Text()
    crossref_password = columns.Text()
    reports_username = columns.Text()
    reports_password = columns.Text()
    reports_project = columns.Text()
    reports_user_id = columns.Text()
    reports_group_id = columns.Text()
    reports_project_id = columns.Text()
    reports_setup_status = columns.Text()
    supported_products = columns.List(columns.Text())
    pilot = columns.Boolean()
    demo = columns.Boolean(index=True)
    demo_id = columns.Text(index=True)
    has_cohort = columns.Boolean(index=True)
    cohort_articles_issns_to_lookup = columns.List(columns.Text())
    cohort_articles_last_updated = columns.DateTime()
    archived = columns.Boolean(default=False, index=True)

if __name__ == "__main__":
    open_cassandra_connection()

    publishers = [
        #'acs',
        'asm',
    ]

    for p in publishers:

        ctr = 0
        dup_ctr = 0
        dups = set()

        print('Checking ' + p + ' ...')
        for ra in Rejected_Articles.objects.filter(publisher_id=p).limit(10000000):

            ctr += 1

            if ra.manuscript_id in dups:
                continue

            dup_list = Rejected_Articles.objects.filter(publisher_id=p, manuscript_id=ra.manuscript_id)

            if len(dup_list) >= 2:
                dup_ctr += 1

                print("\nManuscript " + ra.manuscript_id + " has " + str(len(dup_list)) + " entries.")

                if len(dup_list) == 2 and dup_list[0].updated == dup_list[1].updated:
                    print("2 entries with same updated time stamp, removing 1")
                    i = dup_list[0]
                    i.delete()
                    print("Removed: " + i.manuscript_id + "--" + str(i.rejected_article_id) + "-- " + str(i.updated))

                else:
                    dm = {}
                    for i in dup_list:
                        print(i.manuscript_id + "--" + str(i.rejected_article_id) + "-- " + str(i.updated))
                        dm[i.updated] = i

                    i_max = dm[max(dm.keys())]
                    print("Keep: " + i_max.manuscript_id + "--" + str(i_max.rejected_article_id) + "-- " + str(i_max.updated))

                    dm.pop(i_max.updated)
                    for i in dm.values():
                        i.delete()
                        print("Removed: " + i.manuscript_id + "--" + str(i.rejected_article_id) + "-- " + str(i.updated))

                dups.add(ra.manuscript_id)

        print(str(dup_ctr) + " / " + str(ctr) + " duplicates found for " + p)

    close_cassandra_connection()
