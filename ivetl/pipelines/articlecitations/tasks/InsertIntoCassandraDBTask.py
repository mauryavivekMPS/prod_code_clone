__author__ = 'nmehta'

import csv
import codecs
import json
from datetime import datetime
from ivetl.common import common
from ivetl.celery import app
from ivetl.models.PublishedArticle import Published_Article
from ivetl.models.ArticleCitations import Article_Citations
from ivetl.models.PublisherVizorUpdates import Publisher_Vizor_Updates
from ivetl.pipelines.task import Task


@app.task
class InsertIntoCassandraDBTask(Task):
    taskname = "InsertIntoCassandraDB"
    vizor = common.AC

    CITATION_SOURCE = "Scopus"

    def run_task(self, publisher, job_id, workfolder, tlogger, args):

        file = args[BaseTask.INPUT_FILE]

        count = 0
        today = datetime.today()
        updated = today

        with codecs.open(file, encoding="utf-16") as tsv:

            for line in csv.reader(tsv, delimiter="\t"):

                count += 1
                if count == 1:
                    continue

                publisher = line[0]
                doi = line[1]
                citations = json.loads(line[2])

                for data in citations:

                    #if 'prism:doi' not in data or (data['prism:doi'] == ''):
                    #    continue

                    #if 'prism:coverDate' in data and (data['prism:coverDate'] != ''):
                    #    dop = datetime.strptime(data['prism:coverDate'], '%Y-%m-%d')

                        #if dop > today:
                        #    continue

                    ac = Article_Citations()

                    ac['publisher_id'] = publisher
                    ac['article_doi'] = doi
                    ac['updated'] = updated
                    ac['created'] = updated

                    if 'prism:doi' in data and (data['prism:doi'] != ''):
                        ac['citation_doi'] = data['prism:doi']
                    else:
                        ac['citation_doi'] = data['eid']

                    if 'eid' in data and (data['eid'] != 0):
                        ac['citation_scopus_id'] = data['eid']

                    if 'prism:coverDate' in data and (data['prism:coverDate'] != ''):
                        ac['citation_date'] = datetime.strptime(data['prism:coverDate'], '%Y-%m-%d')

                    if 'dc:creator' in data and (data['dc:creator'] != 0):
                        ac['citation_first_author'] = data['dc:creator']

                    if 'prism:issueIdentifier' in data and (data['prism:issueIdentifier'] != 0):
                        ac['citation_issue'] = data['prism:issueIdentifier']

                    if 'prism:issn' in data and (data['prism:issn'] != 0):
                        ac['citation_journal_issn'] = data['prism:issn']

                    if 'prism:publicationName' in data and (data['prism:publicationName'] != 0):
                        ac['citation_journal_title'] = data['prism:publicationName']

                    if 'prism:pageRange' in data and (data['prism:pageRange'] != 0):
                        ac['citation_pages'] = data['prism:pageRange']

                    ac['citation_source'] = self.CITATION_SOURCE

                    if 'dc:title' in data and (data['dc:title'] != 0):
                        ac['citation_title'] = data['dc:title']

                    if 'prism:volume' in data and (data['prism:volume'] != 0):
                        ac['citation_volume'] = data['prism:volume']

                    ac['citation_count'] = 1

                    ac.save()

                pa = Published_Article()
                pa['publisher_id'] = publisher
                pa['article_doi'] = doi
                #pa['scopus_citation_count'] = len(citations)
                pa['citations_updated_on'] = updated
                pa.update()

                tlogger.info("---")
                tlogger.info(str(count-1) + ". " + publisher + " / " + doi + ": Inserted " + str(len(citations)) + " citations.")

            tsv.close()

            pu = Publisher_Vizor_Updates()
            pu['publisher_id'] = publisher
            pu['vizor_id'] = 'article_citations'
            pu['updated'] = updated
            pu.save()

        self.pipelineCompleted(publisher, self.vizor, job_id)

        args = {}
        args[BaseTask.COUNT] = count

        return args


def toDateTime(month, day, year):

    if year < 99:
        year += 2000

    # date (y, m, d)
    date = datetime(year, month, day)
    return date








