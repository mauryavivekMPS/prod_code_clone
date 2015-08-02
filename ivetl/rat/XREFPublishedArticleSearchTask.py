from __future__ import absolute_import
import csv
import codecs
from time import time
import json
from datetime import timedelta
import re
from datetime import date
from os import makedirs

import requests
from cassandra.cqlengine import connection

from ivetl.rat.CRArticle import CRArticle
from ivetl.models.IssnJournal import Issn_Journal
from ivetl.common import common
from ivetl.celery import app
from ivetl.common.BaseTask import BaseTask


@app.task
class XREFPublishedArticleSearchTask(BaseTask):

    taskname = "XREFPublishedArticleSearch"
    vizor = common.RAT

    ISSN_JNL_QUERY_LIMIT = 1000000

    def run(self, args):

        file = args[0]
        publisher = args[1]
        day = args[2]
        workfolder = args[3]

        path = workfolder + "/" + self.taskname
        makedirs(path, exist_ok=True)

        tlogger = self.getTaskLogger(path, self.taskname)

        target_file_name = path + "/" + publisher + "_" + day + "_" + "xrefpublishedarticlesearch" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\t'
                          'MANUSCRIPT_ID\t'
                          'DATA\n')

        connection.setup([common.CASSANDRA_IP], common.CASSANDRA_KEYSPACE_IV)

        t0 = time()

        # Build Issn Journal List
        issn_journals = {}
        for ij in Issn_Journal.objects.limit(self.ISSN_JNL_QUERY_LIMIT):
            issn_journals[ij.issn] = (ij.journal, ij.publisher)

        count = 0

        with codecs.open(file, encoding="utf-16") as tsv:

            for line in csv.reader(tsv, delimiter="\t"):

                #sleep(2)

                count += 1
                if count == 1:
                    continue

                publisher = line[0]
                manuscript_id = line[1]
                data = json.loads(line[2])

                tlogger.info("\n" + str(count-1) + ". Reading In Rejected Article: " + publisher + " / " + manuscript_id)

                date_of_rejection = data['date_of_rejection']
                title = data['title']

                data['status'] = ''

                dor_parts = date_of_rejection.split('/')
                dor_month = int(dor_parts[0])
                dor_day = int(dor_parts[1])
                dor_year = int(dor_parts[2])

                if dor_year < 99:
                    dor_year += 2000

                # date (y, m, d)
                dor_date = date(dor_year, dor_month, dor_day)
                dop_date = dor_date + timedelta(days=1)

                # api cross ref date format is YYYY-MM-DD, YYYY-MM or YYYY
                #params = urllib.parse.urlencode({'query': title})

                #dop_date_param = "filter=from-pub-date:" + dop_date.strftime('%Y-%m-%d')
                dop_date_param = "filter=from-pub-date:" + dop_date.strftime('%Y-%m')

                #print(title)
                title = self.removeHex(title)
                #print(title)
                title = self.solrEncode(title)

                attempt = 0
                max_attempts = 3

                while attempt < max_attempts:

                    try:
                        url = 'http://api.crossref.org/works?rows=4&' + dop_date_param + '&query=' + title
                        tlogger.info("Searching CrossRef for: " + url)
                        r = requests.get(url, timeout=30)

                        if "Internal Server Error" in str(r.content):
                            print("No match found")
                            data['status'] = "No match found"

                        else:

                            xrefdata = r.json()

                            if 'ok' in xrefdata['status'] and len(xrefdata['message']['items']) > 0:

                                data['status'] = "Match found"

                                for i in xrefdata['message']['items']:

                                    article = CRArticle()
                                    article.setxrefdetails(i, issn_journals)

                                    i["xref_journal"] = article.journal
                                    i["xref_publisher"] = article.publisher
                                    i["xref_publishdate"] = article.publishdate
                                    i["xref_first_author"] = article.author_last_name + ',' + article.author_first_name
                                    i["xref_co_authors_ln_fn"] = ';'.join(article.xrefcoauthors)
                                    i["xref_title"] = article.bptitle
                                    i["xref_doi"] = article.doi
                                    i["doi_lookup_status"] = "Match found"

                                data['xref_results'] = xrefdata

                            else:
                                data['status'] = "No match found"

                            break

                    except Exception:
                        tlogger.info("XREF Search failed. Trying Again")
                        tlogger.info(Exception, exc_info=True)
                        data['status'] = "No match found"

                        attempt += 1

                if attempt >= max_attempts:
                    tlogger.error("!!! XREF Search failed max times !!!")

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


    def removeHex(self, str):
        return re.sub('&.*;', '', str)


    def solrEncode(self, url):
        return url.replace(' ', '+')\
            .replace(':', '\\:')\
            .replace('-', '\\-')\
            .replace('!', '\\!')\
            .replace('(', '\\(')\
            .replace(')', '\\)')\
            .replace('^', '\\^')\
            .replace('[', '\\[')\
            .replace(']', '\\]')\
            .replace('\"', '\\\"')\
            .replace('{', '\\{')\
            .replace('}', '\\}')\
            .replace('~', '\\~')\
            .replace('*', '\\*')\
            .replace('?', '\\?')\
            .replace('|', '\\|')\
            .replace('&', '')\
            .replace(';', '\\;')\
            .replace('/', '\\/')





