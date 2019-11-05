from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl import hwcolumns


class AltmetricsSocialData(Model):
    doi = hwcolumns.LowercaseText(primary_key=True)
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
