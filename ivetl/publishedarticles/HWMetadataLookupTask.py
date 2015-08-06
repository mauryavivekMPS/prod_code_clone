from __future__ import absolute_import
import csv
import codecs
import json
import urllib.parse
import urllib.request
import traceback
import re
import requests
from requests import HTTPError
from time import sleep
from lxml import etree

from ivetl.common import common
from ivetl.celery import app
from ivetl.common.BaseTask import BaseTask
from ivetl.models.PublisherMetadata import PublisherMetadata


@app.task
class HWMetadataLookupTask(BaseTask):

    taskname = "HWMetadataLookup"
    vizor = common.PA

    SASSFS_BASE_URL = 'http://sassfs-index.highwire.org/nlm-pubid/doi?' \
                      'scheme=http%3A%2F%2Fschema.highwire.org%2FPublishing%23role&' \
                      'term=http%3A%2F%2Fschema.highwire.org%2FJournal%2FArticle&'

    SASS_BASE_URL = 'http://sass.highwire.org'

    ISSN_JNL_QUERY_LIMIT = 1000000

    def run_task(self, publisher, job_id, workfolder, tlogger, args):

        file = args[BaseTask.INPUT_FILE]

        pm = PublisherMetadata.filter(publisher_id=publisher).first()
        issn_to_hw_journal_code = pm.issn_to_hw_journal_code

        target_file_name = workfolder + "/" + publisher + "_" + "hwmetadatalookup" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\t'
                          'DOI\t'
                          'DATA\n')

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

                        sleep(1)
                        r = requests.get(url, timeout=30)

                        root = etree.fromstring(r.content)
                        n = root.xpath('//results:results/results:result/results:result-set/results:row/results:atom.href', namespaces=common.ns)

                        if len(n) != 0:
                            href = n[0].text

                            url = self.SASS_BASE_URL + href

                            tlogger.info("Looking up details on SASS:")
                            tlogger.info(url)

                            r = requests.get(url, timeout=30)
                            r.raise_for_status()

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

                            if article_type is None or article_type == '':
                                article_type = "None"

                            data['article_type'] = article_type
                            #print(article_type)

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

                            if subject_category is None or subject_category == '':
                                subject_category = "None"

                            data['subject_category'] = subject_category
                            #print(subject_category)

                        else:
                            tlogger.info("No SASS HREF found for DOI: " + doi)

                        break

                    except HTTPError:
                        raise
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

        self.pipelineCompleted(publisher, self.vizor, job_id)

        args[BaseTask.INPUT_FILE] = target_file_name
        args[BaseTask.COUNT] = count

        return args





