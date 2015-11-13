import csv
import codecs
import json
import requests
import traceback
import urllib.parse
import urllib.request
from lxml import etree
from ivetl.common import common
from ivetl.celery import app
from ivetl.pipelines.task import Task


@app.task
class ScopusCitationLookupTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        file = task_args['input_file']
        total_count = task_args['count']

        target_file_name = work_folder + "/" + publisher_id + "_" + "scopuscitationlookup" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\t'
                          'MANUSCRIPT_ID\t'
                          'DATA\n')

        count = 0
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):
                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                if count == 1:
                    continue  # ignore the header

                publisher = line[0]
                manuscript_id = line[1]
                data = json.loads(line[2])

                tlogger.info("\n" + str(count-1) + ". Retrieving Citations for: " + manuscript_id)

                if data['status'] == "Match found":

                    tlogger.info('http://api.elsevier.com/content/search/index:SCOPUS?httpAccept=application%2Fxml&apiKey=14edf00bcb425d2e3c40d1c1629f80f9&' + urllib.parse.urlencode({'query': 'doi(' + data['xref_doi'] + ')'}))

                    attempt = 0
                    max_attempts = 3
                    while attempt < max_attempts:
                        try:
                            r = requests.get('http://api.elsevier.com/content/search/index:SCOPUS?httpAccept=application%2Fxml&apiKey=14edf00bcb425d2e3c40d1c1629f80f9&' + urllib.parse.urlencode({'query': 'doi(' + data['xref_doi'] + ')'}))

                            root = etree.fromstring(r.content, etree.HTMLParser())
                            n = root.xpath('//entry/eid', namespaces=common.ns)

                            if len(n) != 0:
                                scopus_id = n[0].text

                                data['citation_lookup_status'] = "ID in Scopus"
                                data['scopus_doi_status'] = "DOI in Scopus"
                                data['scopus_id'] = scopus_id

                                tlogger.info('http://api.elsevier.com/content/search/index:SCOPUS?httpAccept=application%2Fjson&apiKey=14edf00bcb425d2e3c40d1c1629f80f9&' + urllib.parse.urlencode({'query': 'refeid(' + scopus_id + ')'}))
                                r = requests.get('http://api.elsevier.com/content/search/index:SCOPUS?httpAccept=application%2Fjson&apiKey=14edf00bcb425d2e3c40d1c1629f80f9&' + urllib.parse.urlencode({'query': 'refeid(' + scopus_id + ')'}))

                                j = r.json()
                                data['citations'] = j['search-results']['opensearch:totalResults']

                                tlogger.info("Scopus Cites = " + str(data['citations']))
                            else:
                                scopus_id = ''
                                tlogger.info("No Scopus Id found for DOI: " + data['xref_doi'])
                                data['scopus_doi_status'] = "No DOI in Scopus"
                                data['citation_lookup_status'] = "No ID in Scopus"
                                data['scopus_id'] = ''

                            break

                        except Exception:
                            tlogger.info("Scopus API failed. Trying Again")
                            print(manuscript_id)
                            traceback.print_exc()
                            data['citation_lookup_status'] = "Scopus API failed"
                            data['scopus_id'] = ''
                            data['scopus_doi_status'] = "Scopus API failed"

                            attempt += 1

                else:
                    tlogger.info(data['status'])

                row = """%s\t%s\t%s\n""" % (publisher,
                                            manuscript_id,
                                            json.dumps(data))

                target_file.write(row)
                target_file.flush()

        target_file.close()

        return {
            'input_file': target_file_name,
            'count': count,
        }
