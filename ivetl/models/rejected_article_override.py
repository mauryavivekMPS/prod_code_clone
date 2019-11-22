from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl import hwcolumns

class RejectedArticleOverride(Model):
    publisher_id = columns.Text(primary_key=True)
    manuscript_id = columns.Text(primary_key=True)
    doi = hwcolumns.LowercaseText(primary_key=True)
    label = columns.Text(required=False) 
