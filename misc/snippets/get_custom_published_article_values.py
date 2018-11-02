#!/usr/bin/env python
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.models import PublishedArticleValues

import os

os.sys.path.append(os.environ['IVETL_ROOT'])


dois_to_check = [
    "10.1074/jbc.RA118.002605",
    "10.1074/jbc.RA117.001329",
    "10.1074/jbc.RA117.000100",
    "10.1074/jbc.RA118.001860",
    "10.1074/jbc.RA117.000728",
    "10.1074/jbc.RA117.000963",
    "10.1074/jbc.RA117.001436",
    "10.1074/jbc.AC117.001649",
    "10.1074/jbc.RA117.001446",
    "10.1074/jbc.RA117.000941",
    "10.1074/jbc.RA117.001207",
    "10.1074/jbc.RA117.000485",
    "10.1074/jbc.RA117.001013",
    "10.1074/jbc.RA117.001382",
    "10.1074/jbc.RA117.000634",
    "10.1074/jbc.RA117.000265",
    "10.1074/jbc.RA117.000922",
    "10.1074/jbc.RA117.000178",
    "10.1074/jbc.RA117.000405",
    "10.1074/jbc.RA117.000106",
    "10.1074/jbc.RA117.000131",
    "10.1074/jbc.M117.806901",
    "10.1074/jbc.M116.758268",
    "10.1074/jbc.M116.758029",
    "10.1074/jbc.M116.760975",
    "10.1074/jbc.M116.766964",
    "10.1074/jbc.M116.756288",
    "10.1074/jbc.M116.771592",
    "10.1074/jbc.M116.764720",
    "10.1074/jbc.M116.759944",
    "10.1074/jbc.M116.755884",
    "10.1074/jbc.M116.760876",
]

if __name__ == "__main__":

    open_cassandra_connection()

    publisher_id = 'asbmb'

    ctr = 0


    for doi in dois_to_check:

        article_value = PublishedArticleValues.objects.filter(publisher_id=publisher_id,
                                                               article_doi=doi.lower(),
                                                               source='custom',
                                                               name='article_type').first()

        if article_value:
            print(article_value.article_doi + "\t" + article_value.value_text)

    close_cassandra_connection()

