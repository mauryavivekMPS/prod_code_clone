from ivetl.pipelines.test_pipelines import PipelineTestCase
from ivetl.pipelines.publishedarticles import UpdatePublishedArticlesPipeline


class PublishedArticlesTestCase(PipelineTestCase):

    def setUp(self):
        self.remove_all_test_publisher_data()
        self.add_test_publisher()

    def tearDown(self):
        self.remove_all_test_publisher_data()

    def test_pipeline_with_poll_and_timeout(self):

        def run_pipeline():
            UpdatePublishedArticlesPipeline.s(
                publisher_id_list=['test'],
                reprocess_all=True,
                articles_per_page=2,
                max_articles_to_process=2
            ).delay()

        # run the pipeline, check for a completed status
        self.poll_and_timeout('test', UpdatePublishedArticlesPipeline.pipeline_name, run_pipeline)
