from __future__ import absolute_import

import codecs
from time import time
import json
import requests
from os import makedirs
import datetime

from cassandra.cqlengine import connection

from ivetl.common import common
from ivetl.celery import app
from ivetl.common.BaseTask import BaseTask
from ivetl.common.PublishedArticle import Published_Article


@app.task
class GetScopusArticleCitationsTask(BaseTask):

    taskname = "GetScopusArticleCitations"
    vizor = common.AC

    ITEMS_PER_PAGE = 25
    QUERY_LIMIT = 500000
    SCOPUS_BASE_URL = 'http://api.elsevier.com/content/search/index:SCOPUS?httpAccept=application%2Fjson&apiKey=14edf00bcb425d2e3c40d1c1629f80f9&'

    def run(self, publisher, day, workfolder, reprocessall, reprocesserrorsonly):

        path = workfolder + "/" + self.taskname
        makedirs(path, exist_ok=True)

        connection.setup([common.CASSANDRA_IP], common.CASSANDRA_KEYSPACE_IV)

        tlogger = self.getTaskLogger(path, self.taskname)

        target_file_name = path + "/" + publisher + "_" + day + "_" + "articlecitations" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\t'
                          'DOI\t'
                          'DATA\n')
        t0 = time()

        count = 0
        errors = False

        articles = Published_Article.objects.filter(publisher_id=publisher).limit(self.QUERY_LIMIT)
        total_articles = len(articles)

        for article in articles:

            count += 1

            tlogger.info("---")
            tlogger.info(str(count) + " of " + str(total_articles) + ". Looking Up Citations for " + publisher + " / " + article.article_doi)
            if article.article_scopus_id is None or article.article_scopus_id == '':
                tlogger.info("Skipping - No Scopus Id")
                continue

            if not reprocessall and article.citations_updated_on is not None:
                if (article.date_of_publication.year + 2) < datetime.datetime.today().year:
                    tlogger.info("Skipping - Citations are already up to date")
                    continue

            if reprocesserrorsonly:
                if article.citations_lookup_error is not True:
                    tlogger.info("Skipping - Only processing Articles with error in looking up citations")
                    continue

            offset = 0
            num_citations = 0
            citations = []

            while offset != -1:

                attempt = 0
                max_attempts = 5
                r = None
                success = False

                #if count >= 10:
                #    break

                while not success and attempt < max_attempts:
                    try:

                        query = 'query=refeid(' + article.article_scopus_id + ')'
                        query += '+AND+pubyear>' + str(article.date_of_publication.year - 1)
                        query += '+AND+pubyear<' + str(article.date_of_publication.year + 3)

                        url = self.SCOPUS_BASE_URL + query
                        url += '&count=' + str(self.ITEMS_PER_PAGE)
                        url += '&start=' + str(offset)

                        tlogger.info("Searching Scopus: " + url)
                        r = requests.get(url, timeout=30)

                        success = True

                    except Exception:
                        attempt += 1
                        tlogger.warning("Error connecting to Scopus API.  Trying again.")

                if success:
                    scopusdata = r.json()

                    if 'search-results' not in scopusdata:
                        offset = -1

                    elif 'entry' in scopusdata['search-results'] and len(scopusdata['search-results']['entry']) > 0:

                        if 'error' in scopusdata['search-results']['entry'][0]:
                            offset = -1
                        else:

                            for i in scopusdata['search-results']['entry']:

                                if 'prism:doi' in i and (i['prism:doi'] != ''):
                                    citations.append(i)
                                    num_citations += 1

                            total_results = int(scopusdata['search-results']['opensearch:totalResults'])
                            if self.ITEMS_PER_PAGE + offset < total_results:
                                offset += self.ITEMS_PER_PAGE
                            else:
                                offset = -1

                    else:
                        offset = -1
                else:
                    pa = Published_Article()
                    pa['publisher_id'] = publisher
                    pa['article_doi'] = article.article_doi
                    pa['citations_lookup_error'] = True
                    pa.update()

                    errors = True

                    tlogger("!!ERROR getting citations.")

            row = """%s\t%s\t%s\n""" % (
                                publisher,
                                article.article_doi,
                                json.dumps(citations))

            target_file.write(row)
            target_file.flush()

            tlogger.info(str(num_citations) + " citations retrieved.")

        target_file.close()

        if errors:
            subject = "!!" + publisher + " / Article Citations - " + day + " - Errors !!"
            text = "Errors getting citations. Manual with reprocess errors to true."
            self.sendEmail(subject, text)

        t1 = time()
        tlogger.info("Rows Processed:   " + str(count))
        tlogger.info("Time Taken:       " + format(t1-t0, '.2f') + " seconds / " + format((t1-t0)/60, '.2f') + " minutes")

        return target_file_name, publisher, day, workfolder








