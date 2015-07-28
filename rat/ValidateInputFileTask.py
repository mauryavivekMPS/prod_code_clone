from __future__ import absolute_import

import csv
import codecs
from time import time
from os import makedirs

from ivetl.common import common
from ivetl.celery import app
from ivetl.common.BaseTask import BaseTask
from ivetl.common.InputFileError import InputFileError


@app.task
class ValidateInputFileTask(BaseTask):

    taskname = "ValidateInputFile"
    vizor = common.RAT

    def run(self, files, publisher, day, workfolder):

        path = workfolder + "/" + self.taskname
        makedirs(path, exist_ok=True)

        tlogger = self.getTaskLogger(path, self.taskname)

        t0 = time()
        totalcount = 0
        foundError = False

        for file in files:

            with codecs.open(file, encoding="utf-16") as tsv:

                count = 0
                for line in csv.reader(tsv, delimiter="\t"):

                    count += 1
                    if count == 1:
                        continue

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
                    input_data['keywords'] = ''
                    input_data['custom'] = ''
                    input_data['funders'] = ''

                    if len(line) >= 12 and line[11].strip() != '':
                        input_data['keywords'] = line[11].strip()

                    if len(line) >= 13 and line[12].strip() != '':
                        input_data['custom'] = line[12].strip()

                    if len(line) >= 14 and line[13].strip() != '':
                        input_data['funders'] = line[13].strip()

                    if len(line) >= 15 and line[14].strip() != '':
                        input_data['published_doi'] = line[14].strip()

                    if input_data['manuscript_id'] == "":
                        tlogger.error("\nLine: " + str(count-1) + ": Checking Rejected Article: " + line[0] + " (" + file + ")")
                        tlogger.error("ERROR: Does not have value for MANUSCRIPT_ID")
                        foundError = True

                    if input_data['date_of_rejection'] == "":
                        tlogger.error("\nLine: " + str(count-1) + ": Checking Rejected Article: " + line[0] + " (" + file + ")")
                        tlogger.error("ERROR: Does not have value for DATE_OF_REJECTION")
                        foundError = True

                    elif not self.validDate(input_data['date_of_rejection']):
                        tlogger.error("\nLine: " + str(count-1) + ": Checking Rejected Article: " + line[0] + " (" + file + ")")
                        tlogger.error("ERROR: Invalid date format for DATE_OF_REJECTION")
                        foundError = True

                    if input_data['reject_reason'] == "":
                        tlogger.error("\nLine: " + str(count-1) + ": Checking Rejected Article: " + line[0] + " (" + file + ")")
                        tlogger.error("ERROR: Does not have value for REJECT_REASON")
                        foundError = True

                    if input_data['title'] == "":
                        tlogger.error("\nLine: " + str(count-1) + ": Checking Rejected Article: " + line[0] + " (" + file + ")")
                        tlogger.error("ERROR: Does not have value for TITLE")
                        foundError = True

                    if input_data['first_author'] == "" and input_data['corresponding_author'] == "" and input_data['co_authors'] == "":
                        tlogger.error("\nLine: " + str(count-1) + ": Checking Rejected Article: " + line[0] + " (" + file + ")")
                        tlogger.error("ERROR: Does not have value for any of the author fields (first, corresponding, co)")
                        foundError = True

                    if input_data['submitted_journal'] == "":
                        tlogger.error("\nLine: " + str(count-1) + ": Checking Rejected Article: " + line[0] + " (" + file + ")")
                        tlogger.error("ERROR: Does not have value for SUBMITTED_JOURNAL")
                        foundError = True

                totalcount += count
                tsv.close()

        t1 = time()

        tlogger.info("Rows Processed:   " + str(totalcount - 1))
        tlogger.info("Time Taken:       " + format(t1-t0, '.2f') + " seconds / " + format((t1-t0)/60, '.2f') + " minutes")

        if foundError is False:
            tlogger.info("No Errors Found")
        else:
            tlogger.error("\n!! ERRORS FOUND !!")
            raise Exception("Validation Errors in Files: " + str(files))

        return files, publisher, day, workfolder


    def validDate(self, date):

        isValid = True

        date_parts = date.split('/')

        if len(date_parts) != 3:
            isValid = False
        else:
            try:
                int(date_parts[0])
                int(date_parts[1])
                int(date_parts[2])

            except ValueError:
                isValid = False

        return isValid






