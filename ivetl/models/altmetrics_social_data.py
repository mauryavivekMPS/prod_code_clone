from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class AltmetricsSocialData(Model):
    doi = columns.Text(primary_key=True)
    altmetrics_id = columns.Integer()
    facebook = columns.Integer()
    blogs = columns.Integer()
    twitter = columns.Integer()
    gplus = columns.Integer()
    news_outlets = columns.Integer()
    wikipedia = columns.Integer()
    video = columns.Integer()
    policy_docs = columns.Integer()
    reddit = columns.Integer()
