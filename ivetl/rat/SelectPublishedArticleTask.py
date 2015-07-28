from __future__ import absolute_import

import csv
import codecs
from time import time
import json
import re
from os import makedirs

from ivetl.rat.CRArticle import CRArticle
from ivetl.rat.AuthorMatchCheck import AuthorMatchCheck
from ivetl.rat.JournalFilterCheck import JournalFilterCheck
from ivetl.common import common
from ivetl.celery import app
from ivetl.common.BaseTask import BaseTask


@app.task
class SelectPublishedArticleTask(BaseTask):

    taskname = "SelectPublishedArticle"
    vizor = common.RAT

    def run(self, args):

        file = args[0]
        publisher = args[1]
        day = args[2]
        workfolder = args[3]

        path = workfolder + "/" + self.taskname
        makedirs(path, exist_ok=True)

        tlogger = self.getTaskLogger(path, self.taskname)

        target_file_name = path + "/" + publisher + "_" + day + "_" + "selectpublishedarticle" + "_" + "target.tab"
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

                tlogger.info("\n" + str(count-1) + ". Reading In Rejected Article: " + publisher + " / " + manuscript_id)

                if data['status'] == "Match found":

                    xref_search_results_json = data['xref_results']
                    #print(xref_search_results_json)

                    xref_matches = xref_search_results_json['message']['items']
                    if 'published_doi' in data and data['published_doi'] != '':
                        xref_matches = filter_out_published_doi(data['published_doi'], xref_matches)

                    xref_article = JournalFilterCheck.check(xref_matches, tlogger)

                    if xref_article is not None:
                        # Check that author last names match
                        print("\n" + str(count-1) + ". Checking Article: " + xref_article["xref_doi"] + " / " + manuscript_id )
                        author_match_check = AuthorMatchCheck.check(data['first_author'], data['corresponding_author'], data['co_authors'],
                                                                    xref_article["xref_first_author"], xref_article["xref_co_authors_ln_fn"],
                                                                    tlogger)

                        if author_match_check.is_match is False:
                            tlogger.info("No Match Found due to mismatching authors\n")

                    if xref_article is None:
                        tlogger.info("No match found due to journal filter check\n")

                    if xref_article is None or author_match_check.is_match is False:
                        data['status'] = "No match found"
                    else:
                        tlogger.info("Match Found")

                        data['status'] = "Match found"
                        data['xref_score'] = xref_article["score"]
                        data['xref_doi'] = xref_article["xref_doi"]
                        data['xref_journal'] = xref_article["xref_journal"]
                        data['xref_publishdate'] = xref_article["xref_publishdate"]
                        data['xref_first_author'] = xref_article["xref_first_author"]
                        data['xref_co_authors_ln_fn'] = xref_article["xref_co_authors_ln_fn"]
                        data['xref_title'] = xref_article["xref_title"]
                        data['author_match_score'] = format(author_match_check.score, '.2f')
                        data['xref_published_publisher'] = xref_article["xref_publisher"]

                        if "ISSN" in xref_article and len(xref_article["ISSN"]) > 0:
                            data['xref_journal_issn'] = xref_article["ISSN"][0]

                        tlogger.info("Matched Title: " + data['xref_title'])
                        tlogger.info("Matched Journal: " + data['xref_journal'] + "\n")

                row = """%s\t%s\t%s\n""" % (
                                        publisher,
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


def filter_out_published_doi(self, published_doi, xref_matches):

    filtered_xref_matches = []

    for xref_match in xref_matches:
        if published_doi != xref_match["xref_doi"]:
            filtered_xref_matches.append(xref_match)

    return filtered_xref_matches






