from ivetl.models import ArticleCitations
from ivetl.pipelines.test_pipelines import PipelineTestCase
from ivetl.pipelines.articlecitations import UpdateArticleCitationsPipeline


class CustomArticleDataTestCase(PipelineTestCase):

    def setUp(self):
        self.remove_all_test_publisher_data()
        self.add_test_publisher()
        self.add_published_articles_data()

    def tearDown(self):
        self.remove_all_test_publisher_data()

    def test_pipeline_with_poll_and_timeout(self):

        def run_pipeline():
            UpdateArticleCitationsPipeline.s(
                publisher_id_list=['test'],
            ).delay()

        # run the pipeline, check for a completed status
        self.poll_and_timeout('test', UpdateArticleCitationsPipeline.pipeline_name, run_pipeline)

        # pull out one of the expected citations
        citation1 = ArticleCitations.objects.get(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-427765',
            citation_doi='10.1002/ajh.23628'
        )

        # check a couple of basic stats
        self.assertEqual(citation1.citation_journal_title, 'American Journal of Hematology')
        self.assertEqual(citation1.citation_scopus_id, '2-s2.0-84893910207')

        # check for a citation from both scopus and crossref
        citation2 = ArticleCitations.objects.get(
            publisher_id='test',
            article_doi='10.1182/blood-2012-11-464685',
            citation_doi='10.3389/fimmu.2015.00015'
        )

        # check that both items are there
        self.assertEqual(citation1.citation_sources, ['Scopus', 'Crossref'])
