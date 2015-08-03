from __future__ import absolute_import

import csv
import codecs
import json
import urllib.parse
import urllib.request
import requests
from lxml import etree
import traceback

from ivetl.common import common
from ivetl.celery import app
from ivetl.common.BaseTask import BaseTask


@app.task
class ScopusIdLookupTask(BaseTask):

    taskname = "ScopusIdLookup"
    vizor = common.PA

    BASE_SCOPUS_URL = 'http://api.elsevier.com/content/search/index:SCOPUS?httpAccept=application%2Fxml&apiKey=14edf00bcb425d2e3c40d1c1629f80f9&'

    def run(self, args):

        publisher = args[BaseTask.PUBLISHER_ID]
        workfolder = args[BaseTask.WORK_FOLDER]
        job_id = args[BaseTask.JOB_ID]
        file = args[BaseTask.INPUT_FILE]

        task_workfolder, tlogger = self.setupTask(workfolder)

        target_file_name = task_workfolder + "/" + publisher + "_" + "scopuscitationlookup" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\t'
                          'DOI\t'
                          'DATA\n')

        t0 = self.taskStarted(publisher, job_id)
        count = 0

        with codecs.open(file, encoding="utf-16") as tsv:

            for line in csv.reader(tsv, delimiter="\t"):

                count += 1
                if count == 1:
                    continue

                publisher = line[0]
                doi = line[1]
                data = json.loads(line[2])

                tlogger.info("---")
                tlogger.info(str(count-1) + ". Retrieving Scopus Id for: " + doi)

                tlogger.info(self.BASE_SCOPUS_URL + urllib.parse.urlencode({'query': 'doi(' + doi + ')'}))

                attempt = 0
                max_attempts = 3
                success = False

                while not success and attempt < max_attempts:
                    try:
                        r = requests.get(self.BASE_SCOPUS_URL + urllib.parse.urlencode({'query': 'doi(' + doi + ')'}), timeout=30)
                        #sleep(2)

                        root = etree.fromstring(r.content, etree.HTMLParser())
                        n = root.xpath('//entry/eid', namespaces=common.ns)

                        if len(n) == 0 and 'ISSN' in data and 'volume' in data and 'issue' in data and 'page' in data:

                            tlogger.info("Looking up using volume/issue/page")

                            query = ''
                            for i in range(len(data['ISSN'])):
                                query += 'ISSN(' + data['ISSN'][i] + ')'
                                if i != len(data['ISSN']) - 1:
                                    query += " OR "

                            query += " AND VOLUME(" + data['volume'] + ")"
                            query += " AND issue(" + data['issue'] + ")"
                            query += " AND pages(" + data['page'] + ")"

                            tlogger.info(self.BASE_SCOPUS_URL + urllib.parse.urlencode({'query': query}))

                            r = requests.get(self.BASE_SCOPUS_URL + urllib.parse.urlencode({'query': query}), timeout=30)
                            root = etree.fromstring(r.content, etree.HTMLParser())
                            n = root.xpath('//entry/eid', namespaces=common.ns)

                        if len(n) != 0:
                            scopus_id = n[0].text

                            data['scopus_id_status'] = "DOI in Scopus"
                            data['scopus_id'] = scopus_id

                            c =root.xpath('//entry/citedby-count', namespaces=common.ns)

                            if len(c) != 0:
                                data['scopus_citation_count'] = c[0].text

                        else:
                            scopus_id = ''
                            tlogger.info("No Scopus Id found for DOI: " + doi)
                            data['scopus_id_status'] = "No DOI in Scopus"
                            data['scopus_id'] = ''

                        success = True

                    except Exception:
                        tlogger.info("Scopus API failed. Trying Again")
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

        self.taskEnded(publisher, job_id, t0, tlogger, count)

        args = {}
        args[BaseTask.PUBLISHER_ID] = publisher
        args[BaseTask.WORK_FOLDER] = workfolder
        args[BaseTask.JOB_ID] = job_id
        args[BaseTask.INPUT_FILE] = target_file_name

        return args






