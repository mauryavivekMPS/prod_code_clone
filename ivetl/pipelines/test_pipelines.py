import time
import unittest
import datetime
from dateutil import parser
from ivetl.models import (PublisherMetadata, PipelineStatus, PublishedArticle, ArticleCitations,
                          PublisherVizorUpdates, PublishedArticleValues, PipelineTaskStatus)
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
            for s in PipelineStatus.objects.filter(publisher_id=publisher_id, pipeline_id=pipeline_name):
                if s.status == 'completed':
                    got_complete_status = True
                    break

            if got_complete_status:
                break

            # wait for next poll
            time.sleep(poll_time)

        self.assertTrue(got_complete_status, "The pipeline didn't complete after 5 minutes - no status message found.")

    def add_test_publisher(self):
        PublisherMetadata.objects.create(
            publisher_id='test',
            name='Test Publisher',
            hw_addl_metadata_available=True,
            issn_to_hw_journal_code={'1528-0020': 'bloodjournal', '0006-4971': 'bloodjournal'},
            published_articles_issns_to_lookup=['1528-0020'],
            published_articles_last_updated=datetime.datetime(2010, 1, 1),
            scopus_api_keys=['f5bb1dbcd2f625d729836dfcaf5eb5f1', 'f5bb1dbcd2f625d729836dfcaf5eb5f1'],
            crossref_username='amersochem',
            crossref_password='crpw966',
            supported_pipelines=[
                'published_articles',
                'custom_article_data',
                'article_citations',
                'rejected_articles'
            ],
        )

    def remove_all_test_publisher_data(self):
        try:
            publisher = PublisherMetadata.objects.get(publisher_id='test')
            PublishedArticle.objects(publisher_id='test').delete()
            PublishedArticleValues.objects(publisher_id='test').delete()
            ArticleCitations.objects(publisher_id='test').delete()
            PipelineStatus.objects(publisher_id='test').delete()
            PublisherVizorUpdates.objects(publisher_id='test').delete()
            publisher.delete()

        except PublisherMetadata.DoesNotExist:
            # it wasn't there, that's ok
            pass

    def add_published_articles_data(self):
                #
        # the articles
        #

        PublishedArticle.create(
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

        PublishedArticle.create(
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

        PublishedArticleValues.create(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-427765',
            source='pa',
            name='article_type',
            value_text='Review Article',
        )

        PublishedArticleValues.create(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-427765',
            source='pa',
            name='subject_category',
            value_text='Red Cells, Iron, And Erythropoiesis',
        )

        PublishedArticleValues.create(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-464685',
            source='pa',
            name='article_type',
            value_text='Immunobiology',
        )

        PublishedArticleValues.create(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-464685',
            source='pa',
            name='subject_category',
            value_text='Immunobiology',
        )

        #
        # some citations
        #

        ArticleCitations.create(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-427765',
            citation_doi='2013-placeholder',
            citation_count=0,
            citation_date=parser.parse('2012-12-31 16:00:00-0800'),
            created=parser.parse('2015-09-07 13:04:46-0700'),
            updated=parser.parse('2015-09-07 13:04:46-0700'),
        )

        ArticleCitations.create(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-427765',
            citation_doi='2014-placeholder',
            citation_count=0,
            citation_date=parser.parse('2012-12-31 16:00:00-0800'),
            created=parser.parse('2015-09-07 13:04:46-0700'),
            updated=parser.parse('2015-09-07 13:04:46-0700'),
        )

        ArticleCitations.create(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-464685',
            citation_doi='2013-placeholder',
            citation_count=0,
            citation_date=parser.parse('2012-12-31 16:00:00-0800'),
            created=parser.parse('2015-09-07 13:04:46-0700'),
            updated=parser.parse('2015-09-07 13:04:46-0700'),
        )

        ArticleCitations.create(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-464685',
            citation_doi='2014-placeholder',
            citation_count=0,
            citation_date=parser.parse('2012-12-31 16:00:00-0800'),
            created=parser.parse('2015-09-07 13:04:46-0700'),
            updated=parser.parse('2015-09-07 13:04:46-0700'),
        )

        ArticleCitations.create(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-464685',
            citation_doi='2015-placeholder',
            citation_count=0,
            citation_date=parser.parse('2012-12-31 16:00:00-0800'),
            created=parser.parse('2015-09-07 13:04:46-0700'),
            updated=parser.parse('2015-09-07 13:04:46-0700'),
        )

    def add_misc_pipeline_status(self):

        #
        # add a number of test publishers
        #

        PublisherMetadata.objects.create(
            publisher_id='blood',
            name='Blood',
            supported_pipelines=[
                'published_articles',
                'custom_article_data',
                'article_citations',
                'rejected_articles'
            ],
        )

        PublisherMetadata.objects.create(
            publisher_id='theoncologist',
            name='The Oncologist',
            supported_pipelines=[
                'published_articles',
                'custom_article_data',
                'rejected_articles'
            ],
        )

        PublisherMetadata.objects.create(
            publisher_id='neuro',
            name='Journal of Neuroscience',
            supported_pipelines=[
                'published_articles',
                'custom_article_data',
                'article_citations',
            ],
        )

        PublisherMetadata.objects.create(
            publisher_id='sagan',
            name='Cosmology Journal',
            supported_pipelines=[
                'published_articles',
                'custom_article_data',
                'article_citations',
                'rejected_articles'
            ],
        )

        #
        # add some pipeline status
        #

        PipelineStatus.objects.create(
            publisher_id='blood',
            pipeline_id='published_articles',
            job_id='20150824_161812054742',
            current_task='ResolvePublishedArticlesData',
            start_time=datetime.datetime(2015, 8, 24, 9, 18, 12),
            end_time=datetime.datetime(2015, 8, 24, 9, 18, 30),
            updated=datetime.datetime(2015, 8, 24, 9, 18, 30),
            duration_seconds=18,
            error_details=None,
            status='completed',
            workfolder='/iv/working/20150824/test/published_articles/20150824_161812054742',
        )

        PipelineStatus.objects.create(
            publisher_id='blood',
            pipeline_id='published_articles',
            job_id='20150825_161812054742',
            current_task='ResolvePublishedArticlesData',
            start_time=datetime.datetime(2015, 8, 25, 12, 11, 12),
            end_time=datetime.datetime(2015, 8, 25, 12, 11, 51),
            updated=datetime.datetime(2015, 8, 25, 12, 11, 51),
            duration_seconds=39,
            error_details=None,
            status='completed',
            workfolder='/iv/working/20150825/test/published_articles/20150825_161812054742',
        )

        PipelineStatus.objects.create(
            publisher_id='blood',
            pipeline_id='article_citations',
            job_id='20150825_161812054752',
            current_task='UpdateArticleCitationsWithCrossref',
            start_time=datetime.datetime(2015, 8, 25, 12, 11, 12),
            end_time=datetime.datetime(2015, 8, 25, 12, 11, 51),
            updated=datetime.datetime(2015, 8, 25, 12, 11, 51),
            duration_seconds=39,
            error_details=None,
            status='completed',
            workfolder='/iv/working/20150921/test/article_citations/20150921_095547135895',
        )

        PipelineTaskStatus.objects.create(
            publisher_id='blood',
            pipeline_id='article_citations',
            job_id='20150825_161812054752',
            task_id='GetScopusArticleCitations',
            start_time=datetime.datetime(2015, 8, 25, 12, 11, 12),
            end_time=datetime.datetime(2015, 8, 25, 12, 11, 21),
            duration_seconds=9,
            error_details=None,
            status='completed',
            updated=datetime.datetime(2015, 8, 25, 12, 11, 21),
            workfolder='/iv/working/20150921/test/article_citations/20150921_095547135895/GetScopusArticleCitations',
        )

        PipelineTaskStatus.objects.create(
            publisher_id='blood',
            pipeline_id='article_citations',
            job_id='20150825_161812054752',
            task_id='InsertScopusIntoCassandra',
            start_time=datetime.datetime(2015, 8, 25, 12, 11, 22),
            end_time=datetime.datetime(2015, 8, 25, 12, 11, 23),
            duration_seconds=1,
            error_details=None,
            status='completed',
            updated=datetime.datetime(2015, 8, 25, 12, 11, 23),
            workfolder='/iv/working/20150921/test/article_citations/20150921_095547135895/InsertScopusIntoCassandra',
        )

        PipelineTaskStatus.objects.create(
            publisher_id='blood',
            pipeline_id='article_citations',
            job_id='20150825_161812054752',
            task_id='UpdateArticleCitationsWithCrossref',
            start_time=datetime.datetime(2015, 8, 25, 12, 11, 24),
            end_time=datetime.datetime(2015, 8, 25, 12, 11, 35),
            duration_seconds=11,
            error_details=None,
            status='completed',
            updated=datetime.datetime(2015, 8, 25, 12, 11, 35),
            workfolder='/iv/working/20150921/test/article_citations/20150921_095547135895/UpdateArticleCitationsWithCrossref',
        )

        PipelineStatus.objects.create(
            publisher_id='neuro',
            pipeline_id='article_citations',
            job_id='20150825_161812054753',
            current_task='UpdateArticleCitationsWithCrossref',
            start_time=datetime.datetime(2015, 8, 25, 12, 11, 12),
            end_time=datetime.datetime(2015, 8, 25, 12, 11, 51),
            updated=datetime.datetime(2015, 8, 25, 12, 11, 51),
            duration_seconds=39,
            error_details=None,
            status='completed',
            workfolder='/iv/working/20150921/test/article_citations/20150825_161812054753',
        )

        PipelineTaskStatus.objects.create(
            publisher_id='neuro',
            pipeline_id='article_citations',
            job_id='20150825_161812054753',
            task_id='GetScopusArticleCitations',
            start_time=datetime.datetime(2015, 8, 25, 12, 11, 12),
            end_time=datetime.datetime(2015, 8, 25, 12, 11, 21),
            duration_seconds=9,
            error_details=None,
            status='completed',
            updated=datetime.datetime(2015, 8, 25, 12, 11, 21),
            workfolder='/iv/working/20150921/test/article_citations/20150825_161812054753/GetScopusArticleCitations',
        )

        PipelineTaskStatus.objects.create(
            publisher_id='neuro',
            pipeline_id='article_citations',
            job_id='20150825_161812054753',
            task_id='InsertScopusIntoCassandra',
            start_time=datetime.datetime(2015, 8, 25, 12, 11, 22),
            end_time=datetime.datetime(2015, 8, 25, 12, 11, 23),
            duration_seconds=1,
            error_details=None,
            status='completed',
            updated=datetime.datetime(2015, 8, 25, 12, 11, 23),
            workfolder='/iv/working/20150921/test/article_citations/20150825_161812054753/InsertScopusIntoCassandra',
        )

        PipelineTaskStatus.objects.create(
            publisher_id='neuro',
            pipeline_id='article_citations',
            job_id='20150825_161812054753',
            task_id='UpdateArticleCitationsWithCrossref',
            start_time=datetime.datetime(2015, 8, 25, 12, 11, 24),
            end_time=datetime.datetime(2015, 8, 25, 12, 11, 35),
            duration_seconds=11,
            error_details=None,
            status='completed',
            updated=datetime.datetime(2015, 8, 25, 12, 11, 35),
            workfolder='/iv/working/20150921/test/article_citations/20150825_161812054753/UpdateArticleCitationsWithCrossref',
        )
