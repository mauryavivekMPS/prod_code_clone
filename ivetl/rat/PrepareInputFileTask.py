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
class PrepareInputFileTask(BaseTask):

    taskname = "PrepareInputFile"
    vizor = common.RAT

    def run(self, args):

        files = args[0]
        publisher = args[1]
        day = args[2]
        workfolder = args[3]

        path = workfolder + "/" + self.taskname
        makedirs(path, exist_ok=True)

        tlogger = self.getTaskLogger(path, self.taskname)

        target_file_name = path + "/" + publisher + "_" + day + "_" + "preparedinput" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\t'
                          'MANUSCRIPT_ID\t'
                          'DATA\n')

        t0 = time()
        total_count = 0

        for file in files:

            with codecs.open(file, encoding="utf-16") as tsv:

                file_count = 0

                for line in csv.reader(tsv, delimiter="\t"):
                    file_count += 1
                    if file_count == 1:
                        continue
                    else:
                        total_count += 1

                    tlogger.info("\n" + str(file_count-1) + ". Reading In Rejected Article: " + line[3])

                    input_data = {}

                    input_data['manuscript_id'] = line[0].strip()
                    input_data['date_of_rejection'] = line[1].strip()
                    input_data['reject_reason'] = line[2].strip()
                    input_data['title'] = line[3].strip()
                    input_data['first_author'] = line[4].strip()
                    input_data['corresponding_author'] = line[5].strip()
                    input_data['co_authors'] = line[6].strip()
                    input_data['subject_category'] = line[7].strip()
                    input_data['editor'] = line[8].strip()
                    input_data['submitted_journal'] = line[9].strip()
                    input_data['article_type'] = line[10].strip()

                    if len(line) >= 12 and line[11].strip() != '':
                        input_data['keywords'] = line[11].strip()

                    if len(line) >= 13 and line[12].strip() != '':
                        input_data['custom'] = line[12].strip()

                    if len(line) >= 14 and line[13].strip() != '':
                        input_data['funders'] = line[13].strip()

                    if len(line) >= 15 and line[14].strip() != '':
                        input_data['published_doi'] = line[14].strip()

                    input_data['source_file_name'] = file

                    row = """%s\t%s\t%s\n""" % (
                                            publisher,
                                            input_data['manuscript_id'],
                                            json.dumps(input_data))

                    target_file.write(row)
                    target_file.flush()

            tsv.close()

        target_file.close()

        t1 = time()
        tlogger.info("Rows Processed:   " + str(total_count - 1))
        tlogger.info("Time Taken:       " + format(t1-t0, '.2f') + " seconds / " + format((t1-t0)/60, '.2f') + " minutes")

        return target_file_name, publisher, day, workfolder
