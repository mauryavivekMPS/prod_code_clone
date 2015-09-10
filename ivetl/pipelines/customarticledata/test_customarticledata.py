import os
from ivetl.common import common
from ivetl.models import Published_Article
from ivetl.pipelines.test_pipelines import PipelineTestCase
from ivetl.pipelines.customarticledata import CustomArticleDataPipeline


class CustomArticleDataTestCase(PipelineTestCase):

    def setUp(self):
        self.remove_all_test_publisher_data()
        self.add_test_publisher()
        self.add_published_articles_data()

    def tearDown(self):
        self.remove_all_test_publisher_data()

    def test_pipeline_with_poll_and_timeout(self):

        def run_pipeline():
            CustomArticleDataPipeline.s(
                publisher_id_list=['test'],
                preserve_incoming_files=True,
                alt_incoming_dir=os.path.join(common.IVETL_ROOT, 'test/incoming')
            ).delay()

        # run the pipeline, check for a completed status
        self.poll_and_timeout('test', 'custom_article_data', run_pipeline)

        # pull the articles and check for the overridden values
        article1 = Published_Article.objects.get(publisher_id='test', article_doi='10.1182/blood-2012-11-427765')
        article2 = Published_Article.objects.get(publisher_id='test', article_doi='10.1182/blood-2012-11-464685')

        # check basic overrides
        self.assertEqual(article1.subject_category, 'Oncology Foo')
        self.assertEqual(article1.custom, 'C1')

        # check explicit "None"
        self.assertEqual(article1.article_type, 'None')

        # check empty value
        self.assertIsNone(article2.custom_2)

