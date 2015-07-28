from __future__ import absolute_import

import csv
import codecs
from time import time
import json
import urllib.parse
import urllib.request
import requests
from lxml import etree
import traceback
from os import makedirs

from ivetl.common import common
from ivetl.celery import app
from ivetl.common.BaseTask import BaseTask


@app.task
class ScopusIdLookupTask(BaseTask):

    taskname = "ScopusIdLookup"
    vizor = common.PA

    def run(self, args):

        file = args[0]
        publisher = args[1]
        day = args[2]
        workfolder = args[3]

        path = workfolder + "/" + self.taskname
        makedirs(path, exist_ok=True)

        tlogger = self.getTaskLogger(path, self.taskname)

        target_file_name = path + "/" + publisher + "_" + day + "_" + "scopuscitationlookup" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\t'
                          'DOI\t'
                          'DATA\n')

        t0 = time()
        count = 0

        with codecs.open(file, encoding="utf-16") as tsv:

            for line in csv.reader(tsv, delimiter="\t"):

                count += 1
                if count == 1:
                    continue

                publisher = line[0]
                doi = line[1]
                data = json.loads(line[2])

                tlogger.info("\n" + str(count-1) + ". Retrieving Scopus Id for: " + doi)

                tlogger.info('http://api.elsevier.com/content/search/index:SCOPUS?httpAccept=application%2Fxml&apiKey=14edf00bcb425d2e3c40d1c1629f80f9&' + urllib.parse.urlencode({'query': 'doi(' + doi + ')'}))

                attempt = 0
                max_attempts = 3
                while attempt < max_attempts:
                    try:
                        r = requests.get('http://api.elsevier.com/content/search/index:SCOPUS?httpAccept=application%2Fxml&apiKey=14edf00bcb425d2e3c40d1c1629f80f9&' + urllib.parse.urlencode({'query': 'doi(' + doi + ')'}), timeout=30)
                        #sleep(2)

                        root = etree.fromstring(r.content, etree.HTMLParser())
                        n = root.xpath('//entry/eid', namespaces=common.ns)

                        if len(n) != 0:
                            scopus_id = n[0].text

                            data['scopus_id_status'] = "DOI in Scopus"
                            data['scopus_id'] = scopus_id

                        else:
                            scopus_id = ''
                            tlogger.info("No Scopus Id found for DOI: " + doi)
                            data['scopus_id_status'] = "No DOI in Scopus"
                            data['scopus_id'] = ''

                        break

                    except Exception:
                        tlogger.info("Scopus API failed. Trying Again")
                        print(doi)
                        traceback.print_exc()
                        data['scopus_id'] = ''
                        data['scopus_id_status'] = "Scopus API failed"

                        attempt += 1

                row = """%s\t%s\t%s\n""" % (publisher,
                                            doi,
                                            json.dumps(data))

                target_file.write(row)
                target_file.flush()

            tsv.close()

        target_file.close()

        t1 = time()
        tlogger.info("Rows Processed:   " + str(count - 1))
        tlogger.info("Time Taken:       " + format(t1-t0, '.2f') + " seconds / " + format((t1-t0)/60, '.2f') + " minutes")

        return target_file_name, publisher, day, workfolder





