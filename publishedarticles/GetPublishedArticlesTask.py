from __future__ import absolute_import

import codecs
from time import time
import json
import requests
from os import makedirs

from ivetl.common import common
from ivetl.celery import app
from ivetl.common.BaseTask import BaseTask


@app.task
class GetPublishedArticlesTask(BaseTask):

    taskname = "GetPublishedArticles"
    vizor = common.PA
    ITEMS_PER_PAGE = 1000

    def run(self, publisher, issns, start_publication_date, day, workfolder):

        from_pub_date_str = start_publication_date.strftime('%Y-%m-%d')
        path = workfolder + "/" + self.taskname
        makedirs(path, exist_ok=True)

        tlogger = self.getTaskLogger(path, self.taskname)

        target_file_name = path + "/" + publisher + "_" + day + "_" + "xrefpublishedarticles" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\t'
                          'DOI\t'
                          'DATA\n')
        t0 = time()

        count = 0

        for issn in issns:

            offset = 0

            while offset != -1:

                attempt = 0
                max_attempts = 3
                r = None
                success = False

                #if count >= 10:
                #    break

                while not success and attempt < max_attempts:
                    try:
                        url = 'http://api.crossref.org/journals/' + issn + '/works'
                        url += '?rows=' + str(self.ITEMS_PER_PAGE)
                        url += '&offset=' + str(offset)
                        url += '&filter=type:journal-article,from-pub-date:' + from_pub_date_str

                        tlogger.info("Searching CrossRef for: " + url)
                        r = requests.get(url, timeout=30)

                        success = True

                    except Exception:
                        attempt += 1
                        tlogger.warning("Error connecting to Crossref API.  Trying again.")
                        if attempt >= max_attempts:
                            raise

                xrefdata = r.json()

                if 'ok' in xrefdata['status'] and len(xrefdata['message']['items']) > 0:

                    for i in xrefdata['message']['items']:

                        row = """%s\t%s\t%s\n""" % (
                            publisher,
                            i['DOI'],
                            json.dumps(i))

                        target_file.write(row)
                        target_file.flush()

                        count += 1

                    offset += self.ITEMS_PER_PAGE

                else:
                    offset = -1



        target_file.close()

        t1 = time()
        tlogger.info("Rows Processed:   " + str(count))
        tlogger.info("Time Taken:       " + format(t1-t0, '.2f') + " seconds / " + format((t1-t0)/60, '.2f') + " minutes")

        return target_file_name, publisher, day, workfolder








