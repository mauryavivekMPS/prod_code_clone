from __future__ import absolute_import

import csv
import codecs
import json

from ivetl.common import common
from ivetl.celery import app
from ivetl.common.BaseTask import BaseTask
from ivetl.connectors.MaxTriesAPIError import MaxTriesAPIError
from ivetl.connectors.ScopusConnector import ScopusConnector
from ivetl.models.PublisherMetadata import PublisherMetadata


@app.task
class ScopusIdLookupTask(BaseTask):

    taskname = "ScopusIdLookup"
    vizor = common.PA

    MAX_ERROR_COUNT = 100

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

        pm = PublisherMetadata.objects.filter(publisher_id=publisher).first()
        connector = ScopusConnector(pm.scopus_api_key)

        t0 = self.taskStarted(publisher, job_id)
        count = 0
        error_count = 0

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

                try:

                    scopus_id, scopus_cited_by = connector.getScopusEntry(doi, data.get('ISSN'),
                                                                          data.get('volume'),
                                                                          data.get('issue'),
                                                                          data.get('page'),
                                                                          tlogger)

                    if scopus_id is not None and scopus_cited_by is not None:

                        data['scopus_id_status'] = "DOI in Scopus"
                        data['scopus_id'] = scopus_id
                        data['scopus_citation_count'] = scopus_cited_by
                    else:

                        tlogger.info("No Scopus Id found for DOI: " + doi)
                        data['scopus_id_status'] = "No DOI in Scopus"
                        data['scopus_id'] = ''

                except MaxTriesAPIError:
                    tlogger.info("Scopus API failed.")
                    data['scopus_id'] = ''
                    data['scopus_id_status'] = "Scopus API failed"
                    error_count += 1

                row = """%s\t%s\t%s\n""" % (publisher,
                                            doi,
                                            json.dumps(data))

                target_file.write(row)
                target_file.flush()

                if error_count >= self.MAX_ERROR_COUNT:
                    raise MaxTriesAPIError(self.MAX_ERROR_COUNT)

            tsv.close()

        target_file.close()

        self.taskEnded(publisher, job_id, t0, tlogger, count)

        args = {}
        args[BaseTask.PUBLISHER_ID] = publisher
        args[BaseTask.WORK_FOLDER] = workfolder
        args[BaseTask.JOB_ID] = job_id
        args[BaseTask.INPUT_FILE] = target_file_name

        return args






