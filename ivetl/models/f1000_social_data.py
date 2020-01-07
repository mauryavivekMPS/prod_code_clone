from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl import hwcolumns


class F1000SocialData(Model):
    doi = hwcolumns.LowercaseText(primary_key=True)
    f1000_id = columns.Integer()
    total_score = columns.Integer()
    num_recommendations = columns.Integer()
    average_score = columns.Decimal()

    __table_name__ = 'f1000_social_data'
