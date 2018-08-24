#!/usr/bin/env python

import os
os.sys.path.append(os.environ['IVETL_ROOT'])

from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.models import SubscriptionCostPerUseByBundleStatDelta



if __name__ == "__main__":

    open_cassandra_connection()

    ctr = 0

    for ius in SubscriptionCostPerUseByBundleStatDelta.objects.filter(publisher_id='aacr', membership_no='03482645').limit(10000000):

        valid_issns = []
        invalid_issns = []

        if ius.bundle_name == 'COMBO Can Disc':
            print("Found a matching row: " + str(ius))
            # ius.bundle_name = 'COMBO + Can Disc'
            ius.delete()

    close_cassandra_connection()
