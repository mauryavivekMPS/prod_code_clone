#!/usr/bin/env python

import os
os.sys.path.append(os.environ['IVETL_ROOT'])

from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.models import RejectedArticles


if __name__ == "__main__":

    open_cassandra_connection()

    ctr = 0

    for ra in RejectedArticles.objects.filter(publisher_id='asbmb').limit(10000000):

        if ra['submitted_journal'] in ['MCP', 'JBC', 'JLR']:
            if ra['submitted_journal'] == 'MCP':
                ra['submitted_journal'] = 'Molecular & Cellular Proteomics'
            elif ra['submitted_journal'] == 'JLR':
                ra['submitted_journal'] = 'Journal of Lipid Research'
            elif ra['submitted_journal'] == 'JBC':
                ra['submitted_journal'] = 'Journal of Biological Chemistry'
            elif ra['submitted_journal'] == 'Journal':
                ra['submitted_journal'] = 'Journal of Biological Chemistry'

            #ra.update()
            ctr += 1

    print("Modified " + str(ctr) + " manuscripts")

    close_cassandra_connection()
