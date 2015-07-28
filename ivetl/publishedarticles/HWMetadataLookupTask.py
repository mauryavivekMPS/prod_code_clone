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
import re

from cassandra.cqlengine import connection

from ivetl.common import common
from ivetl.celery import app
from ivetl.common.BaseTask import BaseTask
from ivetl.common.Metadata import Metadata
from ivetl.common.IssnJournal import Issn_Journal


@app.task
class HWMetadataLookupTask(BaseTask):

    taskname = "HWMetadataLookup"
    vizor = common.PA

    SASSFS_BASE_URL = 'http://sassfs-index.highwire.org/nlm-pubid/doi?' \
                      'scheme=http%3A%2F%2Fschema.highwire.org%2FPublishing%23role&' \
                      'term=http%3A%2F%2Fschema.highwire.org%2FJournal%2FArticle&'

    SASS_BASE_URL = 'http://sass.highwire.org'

    ISSN_JNL_QUERY_LIMIT = 1000000


    def run(self, args):

        file = args[0]
        publisher = args[1]
        day = args[2]
        workfolder = args[3]

        path = workfolder + "/" + self.taskname
        makedirs(path, exist_ok=True)

        tlogger = self.getTaskLogger(path, self.taskname)

        connection.setup([common.CASSANDRA_IP], common.CASSANDRA_KEYSPACE_IV)

        m = Metadata.filter(publisher_id=publisher).first()
        hw_metadata_available = m.hw_addl_metadata_source
        issn_to_hw_journal_code = m.issn_to_hw_journal_code

        if hw_metadata_available is False:
            tlogger.info("HighWire Metadata not available for " + publisher)
            tlogger.info("Skipping to next task")

            return file, publisher, day, workfolder

        target_file_name = path + "/" + publisher + "_" + day + "_" + "hwmetadatalookup" + "_" + "target.tab"
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

                tlogger.info("\n" + str(count-1) + ". Retrieving HW Metadata for: " + doi)

                hw_journal_code = '/'
                if 'ISSN' in data and (len(data['ISSN']) > 0) and data['ISSN'][0] in issn_to_hw_journal_code:
                    hw_journal_code = "/" + issn_to_hw_journal_code[data['ISSN'][0]]

                value = urllib.parse.urlencode({'value': doi})
                url = self.SASSFS_BASE_URL + 'under=' + hw_journal_code + '&' + value

                tlogger.info("Looking up HREF on SASSFS:")
                tlogger.info(url)

                attempt = 0
                max_attempts = 3
                while attempt < max_attempts:
                    try:
                        r = requests.get(url, timeout=30)

                        root = etree.fromstring(r.content)
                        n = root.xpath('//results:results/results:result/results:result-set/results:row/results:atom.href', namespaces=common.ns)

                        if len(n) != 0:
                            href = n[0].text

                            url = self.SASS_BASE_URL + href

                            tlogger.info("Looking up details on SASS:")
                            tlogger.info(url)

                            r = requests.get(url, timeout=30)
                            root = etree.fromstring(r.content)

                            # Article Type
                            article_type = None
                            at = root.xpath('./nlm:article-categories/nlm:subj-group[@subj-group-type="leader"]/nlm:subject', namespaces=common.ns)

                            if len(at) == 0:
                                at = root.xpath('./nlm:article-categories/nlm:subj-group[@subj-group-type="heading"]/nlm:subject', namespaces=common.ns)

                            if len(at) == 0:
                                at = root.xpath('./nlm:article-categories/nlm:subj-group[@subj-group-type="heading"]//nlm:subj-group[@subj-group-type="display-group"]/nlm:subject[@content-type="original"]', namespaces=common.ns)

                            if len(at) == 0:
                                at = root.xpath('./nlm:article-categories/nlm:subj-group[@subj-group-type="heading"]//nlm:subj-group[@subj-group-type="display-group"]/nlm:subject[@content-type="display-singular"]', namespaces=common.ns)

                            if len(at) != 0:
                                article_type = at[0].text
                                article_type = re.sub("<.*?>", "", article_type)
                                article_type = article_type.strip(' \t\r\n')
                                article_type = article_type.replace('\n', ' ')
                                article_type = article_type.replace('\t', ' ')
                                article_type = article_type.replace('\r', ' ')
                                article_type = article_type.title()

                            if article_type is None:
                                article_type = "None"

                            data['article_type'] = article_type
                            print(article_type)

                            subject_category = None
                            sc = root.xpath('./nlm:article-categories/nlm:subj-group[@subj-group-type="hwp-journal-coll"]/nlm:subject', namespaces=common.ns)

                            if len(sc) != 0:
                                subject_category = sc[0].text
                                subject_category = re.sub("<.*?>", "", subject_category)
                                subject_category = subject_category.strip(' \t\r\n')
                                subject_category = subject_category.replace('\n', ' ')
                                subject_category = subject_category.replace('\t', ' ')
                                subject_category = subject_category.replace('\r', ' ')
                                subject_category = subject_category.title()

                            if subject_category is None:
                                subject_category = "None"

                            data['subject_category'] = subject_category
                            print(subject_category)

                        else:
                            tlogger.info("No SASS HREF found for DOI: " + doi)

                        break

                    except Exception:
                        tlogger.info("SASSFS or SASS API failed. Trying Again")
                        print(doi)
                        print(url)
                        traceback.print_exc()

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





