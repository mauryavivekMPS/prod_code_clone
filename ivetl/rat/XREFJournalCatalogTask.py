from __future__ import absolute_import


from time import time
import requests
import datetime

from cassandra.cqlengine import connection
from cassandra.cqlengine.query import BatchQuery

from ivetl.common.IssnJournal import Issn_Journal
from ivetl.common import common
from ivetl.celery import app
from ivetl.common.BaseTask import BaseTask


@app.task
class XREFJournalCatalogTask(BaseTask):

    taskname = "XREFJournalCatalog"
    vizor = common.RAT

    ITEMS_PER_PAGE = 50

    def run(self):

        connection.setup([common.CASSANDRA_IP], common.CASSANDRA_KEYSPACE_IV)

        day = datetime.datetime.today().strftime('%Y%m%d')

        path = common.BASE_WORK_DIR + day + "/" + self.taskname
        tlogger = self.getTaskLogger(path, self.taskname)

        t0 = time()

        count = 0
        offset = 0

        while offset != -1:

            attempt = 0
            max_attempts = 3
            r = None
            success = False

            while not success and attempt < max_attempts:
                try:
                    url = 'http://api.crossref.org/journals?rows=' + str(self.ITEMS_PER_PAGE) + '&offset=' + str(offset)
                    tlogger.info("Searching CrossRef for: " + url)
                    r = requests.get(url)

                    success = True

                except Exception:
                    attempt += 1
                    tlogger.warning("Error connecting to Crossref API.  Trying again.")
                    if attempt > max_attempts:
                        raise

            xrefdata = r.json()

            if 'ok' in xrefdata['status'] and len(xrefdata['message']['items']) > 0:

                b = BatchQuery()

                for i in xrefdata['message']['items']:


                    issn1 = ""
                    if len(i['ISSN']) > 0:
                        issn1 = i['ISSN'][0].strip()

                    issn2 = ""
                    if len(i['ISSN']) > 1:
                        issn2 = i['ISSN'][1].strip()

                    journal = i['title']
                    publisher = i['publisher']

                    count += 1

                    if issn1 != "":
                        Issn_Journal.batch(b).create(issn=issn1, journal=journal, publisher=publisher)
                        #print(issn1)

                    if issn2 != "":
                        Issn_Journal.batch(b).create(issn=issn2, journal=journal, publisher=publisher)
                        #print(issn2)

                    #print(issn1 + "," + issn2 + ":: " + journal + " / " + publisher)

                b.execute()
                offset += self.ITEMS_PER_PAGE

            else:
                offset = -1

        t1 = time()
        tlogger.info("Rows Processed:   " + str(count))
        tlogger.info("Time Taken:       " + format(t1-t0, '.2f') + " seconds / " + format((t1-t0)/60, '.2f') + " minutes")

        return





