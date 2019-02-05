from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl.models import PublisherUser, PublisherJournal
from ivetl.common import common


class PublisherMetadata(Model):
    publisher_id = columns.Text(primary_key=True)
    name = columns.Text()
    note = columns.Text()
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
    scopus_key_setup_status = columns.Text()
    supported_product_groups = columns.List(columns.Text())  # type: list
    supported_products = columns.List(columns.Text())  # type: list
    pilot = columns.Boolean()
    demo = columns.Boolean(index=True)
    demo_id = columns.Text(index=True)
    has_cohort = columns.Boolean(index=True)
    cohort_articles_issns_to_lookup = columns.List(columns.Text())
    cohort_articles_last_updated = columns.DateTime()
    ac_databases = columns.List(columns.Text())
    archived = columns.Boolean(default=False, index=True)

    @property
    def display_name(self):
        return self.name or self.publisher_id

    @property
    def supports_scopus(self):
        return True if self.scopus_api_keys else False

    @property
    def supports_crossref(self):
        return True if self.crossref_username and self.crossref_password else False

    @property
    def all_issns(self):
        all_issns = []
        for j in PublisherJournal.objects.filter(publisher_id=self.publisher_id, product_id='published_articles'):
            all_issns.append(j.electronic_issn)
            all_issns.append(j.print_issn)
        return all_issns

    @property
    def all_datasources(self):
        all_datasources_for_publisher = set()
        for product_group_id in self.supported_product_groups:
            all_datasources_for_publisher.update(common.PRODUCT_GROUP_BY_ID[product_group_id]['tableau_datasources'])
        return all_datasources_for_publisher

    @property
    def all_workbooks(self):
        all_workbooks_for_publisher = set()
        for product_group_id in self.supported_product_groups:
            all_workbooks_for_publisher.update(common.PRODUCT_GROUP_BY_ID[product_group_id]['tableau_workbooks'])
        return all_workbooks_for_publisher

    def users(self):
        return PublisherUser.objects.allow_filtering().filter(publisher_id=self.publisher_id)

    @property
    def supports_impact_vizor(self):
        return 'impact_vizor' in self.supported_product_groups

    @property
    def supports_usage_vizor(self):
        return 'usage_vizor' in self.supported_product_groups
