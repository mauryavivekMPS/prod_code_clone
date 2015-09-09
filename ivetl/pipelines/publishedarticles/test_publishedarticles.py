from ivetl.pipelines.test_pipelines import PipelineTestCase
from ivetl.pipelines.publishedarticles import UpdatePublishedArticlesPipeline


class PublishedArticlesTestCase(PipelineTestCase):

    def setUp(self):
        self.remove_test_publisher()
        self.add_test_publisher()

    def tearDown(self):
        self.remove_test_publisher()
        pass

    def test_pipeline_with_poll_and_timeout(self):

        def run_published_articles():
            UpdatePublishedArticlesPipeline.s(
                publisher_id_list=['test'],
                reprocess_all=True,
                articles_per_page=2,
                max_articles_to_process=2
            ).delay()

        self.poll_and_timeout('test', 'published_articles', run_published_articles)
