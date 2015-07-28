from __future__ import absolute_import

import csv
import codecs
from time import time
import json
from os import makedirs

from ivetl.common import common
from ivetl.celery import app
from ivetl.common.BaseTask import BaseTask


@app.task
class PrepareForDBInsertTask(BaseTask):

    taskname = "PrepareForDBInsert"
    vizor = common.RAT


    def run(self, args):

        file = args[0]
        publisher = args[1]
        day = args[2]
        workfolder = args[3]

        path = workfolder + "/" + self.taskname
        makedirs(path, exist_ok=True)

        tlogger = self.getTaskLogger(path, self.taskname)

        target_file_name = path + "/" + publisher + "_" + day + "_" + "preparefordbinsert" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\t'
                          'MANUSCRIPT_ID\t'
                          'DATA\n')

        t0 = time()
        count = 0

        with codecs.open(file, encoding="utf-16") as tsv:

            for line in csv.reader(tsv, delimiter="\t"):

                count += 1
                if count == 1:
                    continue

                publisher = line[0]
                manuscript_id = line[1]
                data = json.loads(line[2])

                tlogger.info("\n" + str(count-1) + ". Preparing record: " + publisher + " / " + manuscript_id)

                if data['status'] == "No match found":
                    data['status'] = "Not Published"

                if data['status'] == "Match found" and data['citation_lookup_status'] == "ID in Scopus" and data['citations'] == "0":
                    data['status'] = "Published & Not Cited"

                if data['status'] == "Match found" and data['citation_lookup_status'] == "No ID in Scopus":
                    data['status'] = "Published & Citation Info Unavailable"

                if data['status'] == "Match found" and data['citation_lookup_status'] == "ID in Scopus" and data['citations'] != "0":
                    data['status'] = "Published & Cited"

                row = """%s\t%s\t%s\n""" % (publisher,
                                            manuscript_id,
                                            json.dumps(data))

                target_file.write(row)
                target_file.flush()

            tsv.close()

        target_file.close()

        t1 = time()
        tlogger.info("Rows Processed:   " + str(count - 1))
        tlogger.info("Time Taken:       " + format(t1-t0, '.2f') + " seconds / " + format((t1-t0)/60, '.2f') + " minutes")

        return target_file_name, publisher, day, workfolder






