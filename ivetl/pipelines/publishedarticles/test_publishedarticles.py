import datetime
import time
from ivetl.models import Pipeline_Status
from ivetl.pipelines.test_pipelines import PipelineTestCase
from ivetl.pipelines.publishedarticles import UpdatePublishedArticlesPipeline


class PublishedArticlesTestCase(PipelineTestCase):

    def setUp(self):
        self.remove_test_publisher()
        self.add_test_publisher()

    def tearDown(self):
        # remove other stuff
        # self.remove_test_publisher()
        pass

    def test_pipeline_with_poll_and_timeout(self):

        # run the entire pipeline async, assumes celery worker is running, obviously
        UpdatePublishedArticlesPipeline.s(
            publisher_id_list=['test'],
            reprocess_all=True,
            articles_per_page=2,
            max_articles_to_process=2
        ).delay()

        # poll for results every 2 seconds, timeout after 2 minutes
        timeout_in_seconds = 60 * 2
        start_time = datetime.datetime.now()

        got_complete_status = False
        while (datetime.datetime.now() - start_time).seconds < timeout_in_seconds:

            # look for a single "completed" status line
            for s in Pipeline_Status.objects.filter(publisher_id='test', pipeline_id='published_articles'):
                if s.status == 'completed':
                    got_complete_status = True
                    break

            # wait 10 seconds for next poll
            time.sleep(2)

        self.assertTrue(got_complete_status, "The pipeline didn't complete after 5 minutes - no status message found.")
