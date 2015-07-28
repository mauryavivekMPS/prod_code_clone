from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Metadata(Model):

    publisher_id = columns.Text(primary_key=True)
    file_addl_metadata_source = columns.Boolean()
    hw_addl_metadata_journalcodes = columns.Text()
    hw_addl_metadata_source = columns.Boolean()
    issn = columns.Text()
    last_updated_date = columns.DateTime()
    status = columns.Boolean()
    issn_to_hw_journal_code = columns.Map(columns.Text(), columns.Text())
