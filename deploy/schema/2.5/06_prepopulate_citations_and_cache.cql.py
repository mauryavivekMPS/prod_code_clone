#!/usr/bin/env python

import os
os.sys.path.append(os.environ['IVETL_ROOT'])

import json
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.alerts import CHECKS


class Published_Article_By_Cohort(Model):
    publisher_id = columns.Text(primary_key=True)
    is_cohort = columns.Boolean(primary_key=True)
    article_doi = columns.Text(primary_key=True)
    article_scopus_id = columns.Text()
    updated = columns.DateTime()


class Article_Citations(Model):
    publisher_id = columns.Text(primary_key=True)
    article_doi = columns.Text(primary_key=True)
    citation_doi = columns.Text(primary_key=True)
    citation_date = columns.DateTime()
    citation_first_author = columns.Text()
    citation_issue = columns.Text()
    citation_journal_issn = columns.Text()
    citation_journal_title = columns.Text()
    citation_pages = columns.Text()
    citation_scopus_id = columns.Text()
    citation_sources = columns.List(columns.Text())
    citation_source_scopus = columns.Boolean()
    citation_source_xref = columns.Boolean()
    citation_title = columns.Text()
    citation_volume = columns.Text()
    citation_count = columns.Integer()
    created = columns.DateTime()
    updated = columns.DateTime()
    is_cohort = columns.Boolean()


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


class PublishedArticle(Model):
    publisher_id = columns.Text(primary_key=True)
    article_doi = columns.Text(primary_key=True)
    article_issue = columns.Text()
    article_journal = columns.Text()
    article_journal_issn = columns.Text()
    article_pages = columns.Text()
    article_publisher = columns.Text()
    article_scopus_id = columns.Text()
    article_title = columns.Text()
    article_type = columns.Text()
    article_volume = columns.Text()
    citations_lookup_error = columns.Boolean()
    citations_updated_on = columns.DateTime()
    co_authors = columns.Text()
    created = columns.DateTime()
    custom = columns.Text()
    custom_2 = columns.Text()
    custom_3 = columns.Text()
    date_of_publication = columns.DateTime()
    date_of_rejection = columns.DateTime()
    editor = columns.Text()
    first_author = columns.Text()
    from_rejected_manuscript = columns.Boolean()
    has_abstract = columns.Boolean()
    hw_metadata_retrieved = columns.Boolean()
    is_cohort = columns.Boolean()
    is_open_access = columns.Text()
    rejected_manuscript_editor = columns.Text()
    rejected_manuscript_id = columns.Text()
    scopus_citation_count = columns.Integer()
    subject_category = columns.Text()
    month_usage_03 = columns.Integer()
    month_usage_06 = columns.Integer()
    month_usage_09 = columns.Integer()
    month_usage_12 = columns.Integer()
    month_usage_24 = columns.Integer()
    month_usage_36 = columns.Integer()
    month_usage_48 = columns.Integer()
    month_usage_60 = columns.Integer()
    month_usage_full_03 = columns.Integer()
    month_usage_full_06 = columns.Integer()
    month_usage_full_09 = columns.Integer()
    month_usage_full_12 = columns.Integer()
    month_usage_full_24 = columns.Integer()
    month_usage_full_36 = columns.Integer()
    month_usage_full_48 = columns.Integer()
    month_usage_full_60 = columns.Integer()
    month_usage_pdf_03 = columns.Integer()
    month_usage_pdf_06 = columns.Integer()
    month_usage_pdf_09 = columns.Integer()
    month_usage_pdf_12 = columns.Integer()
    month_usage_pdf_24 = columns.Integer()
    month_usage_pdf_36 = columns.Integer()
    month_usage_pdf_48 = columns.Integer()
    month_usage_pdf_60 = columns.Integer()
    month_usage_abstract_03 = columns.Integer()
    month_usage_abstract_06 = columns.Integer()
    month_usage_abstract_09 = columns.Integer()
    month_usage_abstract_12 = columns.Integer()
    month_usage_abstract_24 = columns.Integer()
    month_usage_abstract_36 = columns.Integer()
    month_usage_abstract_48 = columns.Integer()
    month_usage_abstract_60 = columns.Integer()
    usage_start_date = columns.DateTime()
    mendeley_saves = columns.Integer()
    citation_count = columns.Integer()
    updated = columns.DateTime()


class Attribute_Values(Model):
    publisher_id = columns.Text(partition_key=True)
    name = columns.Text(primary_key=True)
    values_json = columns.Text()


if __name__ == "__main__":
    open_cassandra_connection()

    for p in Publisher_Metadata.objects.all():
        print('Looking at publisher: %s' % p.publisher_id)

        print('Counting citations...')

        articles = Published_Article_By_Cohort.objects.filter(publisher_id=p.publisher_id).limit(500000)
        for a in articles:
            citation_count = Article_Citations.objects.filter(publisher_id=p.publisher_id, article_doi=a.article_doi).limit(500000).count()
            PublishedArticle.objects(publisher_id=p.publisher_id, article_doi=a.article_doi).update(
                citation_count=citation_count,
            )

        print('Done')

        print('Collecting attribute values...')
        all_articles = PublishedArticle.objects.filter(publisher_id=p.publisher_id)
        value_names = set()

        # look through all the alerts for published_article values
        for check_id, check in CHECKS.items():
            for f in check.get('filters', []):
                if f['table'] == 'published_article':
                    value_names.add(f['name'])

        for name in value_names:
            values = set()
            for article in all_articles:
                if article[name]:
                    values.add(article[name])

            if len(values):
                print('\t%s: %s' % (name, len(values)))

            Attribute_Values.objects(
                publisher_id=p.publisher_id,
                name='published_article.' + name,
            ).update(
                values_json=json.dumps(list(values))
            )

        print('Done')

    close_cassandra_connection()



