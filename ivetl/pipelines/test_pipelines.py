import time
import unittest
import datetime
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

            # wait 10 seconds for next poll
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
        )

    def remove_test_publisher(self):
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
