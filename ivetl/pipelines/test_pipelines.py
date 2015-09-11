import time
import unittest
import datetime
from dateutil import parser
from ivetl.models import (Publisher_Metadata, Pipeline_Status, Published_Article, Article_Citations,
                          Publisher_Vizor_Updates, Published_Article_Values)
from ivetl.celery import open_cassandra_connection, close_cassandra_connection


class PipelineTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        open_cassandra_connection()

    @classmethod
    def tearDownClass(cls):
        close_cassandra_connection()

    def poll_and_timeout(self, publisher_id, pipeline_name, pipeline_function, timeout=120, poll_time=2):

        pipeline_function()

        timeout_in_seconds = timeout
        start_time = datetime.datetime.now()

        got_complete_status = False
        while (datetime.datetime.now() - start_time).seconds < timeout_in_seconds:
            # look for a single "completed" status line
            for s in Pipeline_Status.objects.filter(publisher_id=publisher_id, pipeline_id=pipeline_name):
                if s.status == 'completed':
                    got_complete_status = True
                    break

            if got_complete_status:
                break

            # wait for next poll
            time.sleep(poll_time)

        self.assertTrue(got_complete_status, "The pipeline didn't complete after 5 minutes - no status message found.")

    def add_test_publisher(self):
        Publisher_Metadata.objects.create(
            publisher_id='test',
            hw_addl_metadata_available=True,
            issn_to_hw_journal_code={'1528-0020': 'bloodjournal', '0006-4971': 'bloodjournal'},
            published_articles_issns_to_lookup=['1528-0020'],
            published_articles_last_updated=datetime.datetime(2010, 1, 1),
            scopus_api_keys=['f5bb1dbcd2f625d729836dfcaf5eb5f1', 'f5bb1dbcd2f625d729836dfcaf5eb5f1'],
            crossref_username='amersochem',
            crossref_password='crpw966',
        )

    def remove_all_test_publisher_data(self):
        try:
            publisher = Publisher_Metadata.objects.get(publisher_id='test')
            Published_Article.objects(publisher_id='test').delete()
            Published_Article_Values.objects(publisher_id='test').delete()
            Article_Citations.objects(publisher_id='test').delete()
            Pipeline_Status.objects(publisher_id='test').delete()
            Publisher_Vizor_Updates.objects(publisher_id='test').delete()
            publisher.delete()

        except Publisher_Metadata.DoesNotExist:
            # it wasn't there, that's ok
            pass

    def add_published_articles_data(self):
                #
        # the articles
        #

        Published_Article.create(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-427765',
            article_issue='6',
            article_journal='Blood',
            article_journal_issn='0006-4971',
            article_pages='885-892',
            article_publisher=None,
            article_scopus_id='2-s2.0-84886902763',
            article_title='The gut in iron homeostasis: role of HIF-2 under normal and pathological conditions',
            article_type='Review Article',
            article_volume='122',
            citations_lookup_error=None,
            citations_updated_on=None,
            co_authors='Matak,P.; Peyssonnaux,C.; ',
            created=parser.parse('2015-09-07 13:04:46-0700'),
            custom=None,
            custom_2=None,
            custom_3=None,
            date_of_publication=parser.parse('2013-05-14 17:00:00-0700'),
            editor=None,
            first_author='Mastrogiannaki,M.',
            hw_metadata_retrieved=False,
            is_open_access='No',
            scopus_citation_count=14,
            subject_category='Red Cells, Iron, And Erythropoiesis',
            updated=parser.parse('2015-09-07 13:04:46-0700'),
        )

        Published_Article.create(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-464685',
            article_issue='6',
            article_journal='Blood',
            article_journal_issn='0006-4971',
            article_pages='922-931',
            article_publisher=None,
            article_scopus_id='2-s2.0-84886895500',
            article_title='The co-receptor BTLA negatively regulates human V\xa09V\xa02 T-cell proliferation: a potential way of immune escape for lymphoma cells',
            article_type='Immunobiology',
            article_volume='122',
            citations_lookup_error=None,
            citations_updated_on=None,
            co_authors='Fauriat,C.; Orlanducci,F.; Thibult,M.-L.; Pastor,S.; Fitzgibbon,J.; Bouabdallah,R.; Xerri,L.; Olive,D.; ',
            created=parser.parse('2015-09-07 13:04:46-0700'),
            custom=None,
            custom_2=None,
            custom_3=None,
            date_of_publication=parser.parse('2013-05-20 17:00:00-0700'),
            editor=None,
            first_author='Gertner-Dardenne,J.',
            hw_metadata_retrieved=False,
            is_open_access='No',
            scopus_citation_count=16,
            subject_category='Immunobiology',
            updated=parser.parse('2015-09-07 13:04:46-0700'),
        )

        #
        # their override values
        #

        Published_Article_Values.create(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-427765',
            source='pa',
            name='article_type',
            value_text='Review Article',
        )

        Published_Article_Values.create(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-427765',
            source='pa',
            name='subject_category',
            value_text='Red Cells, Iron, And Erythropoiesis',
        )

        Published_Article_Values.create(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-464685',
            source='pa',
            name='article_type',
            value_text='Immunobiology',
        )

        Published_Article_Values.create(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-464685',
            source='pa',
            name='subject_category',
            value_text='Immunobiology',
        )

        #
        # some citations
        #

        Article_Citations.create(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-427765',
            citation_doi='2013-placeholder',
            citation_count=0,
            citation_date=parser.parse('2012-12-31 16:00:00-0800'),
            created=parser.parse('2015-09-07 13:04:46-0700'),
            updated=parser.parse('2015-09-07 13:04:46-0700'),
        )

        Article_Citations.create(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-427765',
            citation_doi='2014-placeholder',
            citation_count=0,
            citation_date=parser.parse('2012-12-31 16:00:00-0800'),
            created=parser.parse('2015-09-07 13:04:46-0700'),
            updated=parser.parse('2015-09-07 13:04:46-0700'),
        )

        Article_Citations.create(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-464685',
            citation_doi='2013-placeholder',
            citation_count=0,
            citation_date=parser.parse('2012-12-31 16:00:00-0800'),
            created=parser.parse('2015-09-07 13:04:46-0700'),
            updated=parser.parse('2015-09-07 13:04:46-0700'),
        )

        Article_Citations.create(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-464685',
            citation_doi='2014-placeholder',
            citation_count=0,
            citation_date=parser.parse('2012-12-31 16:00:00-0800'),
            created=parser.parse('2015-09-07 13:04:46-0700'),
            updated=parser.parse('2015-09-07 13:04:46-0700'),
        )

        Article_Citations.create(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-464685',
            citation_doi='2015-placeholder',
            citation_count=0,
            citation_date=parser.parse('2012-12-31 16:00:00-0800'),
            created=parser.parse('2015-09-07 13:04:46-0700'),
            updated=parser.parse('2015-09-07 13:04:46-0700'),
        )