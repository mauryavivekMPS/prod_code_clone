from __future__ import absolute_import
import csv
import codecs
import json
from datetime import datetime

from ivetl.common import common
from ivetl.celery import app
from ivetl.common.BaseTask import BaseTask
from ivetl.models.PublishedArticle import Published_Article
from ivetl.models.PublisherVizorUpdates import Publisher_Vizor_Updates
from ivetl.models.PublisherMetadata import PublisherMetadata
from ivetl.models.ArticleCitations import Article_Citations


@app.task
class InsertIntoCassandraDBTask(BaseTask):

    taskname = "InsertIntoCassandraDB"
    vizor = common.PA

    def run(self, args):

        publisher = args[BaseTask.PUBLISHER_ID]
        workfolder = args[BaseTask.WORK_FOLDER]
        job_id = args[BaseTask.JOB_ID]
        file = args[BaseTask.INPUT_FILE]

        task_workfolder, tlogger = self.setupTask(workfolder)

        t0 = self.taskStarted(publisher, job_id)
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
                data = json.loads(line[2])

                pa = Published_Article()

                existing_record = Published_Article.objects.filter(publisher_id=publisher, article_doi=doi).first()

                if existing_record:
                    pa = existing_record

                pa['publisher_id'] = publisher
                pa['article_doi'] = doi
                pa['updated'] = updated

                if pa['created'] is None or pa['created'] == '':
                    pa['created'] = updated


                if 'issue' in data and (data['issue'] != ''):
                    pa['article_issue'] = data['issue']

                if 'container-title' in data and (len(data['container-title']) > 0):
                    pa['article_journal'] = data['container-title'][0]

                if 'ISSN' in data and (len(data['ISSN']) > 0):
                    pa['article_journal_issn'] = data['ISSN'][0]

                if 'page' in data and (data['page'] != ''):
                    pa['article_pages'] = data['page']

                if 'scopus_id' in data and (data['scopus_id'] != ''):
                    pa['article_scopus_id'] = data['scopus_id']

                if 'title' in data and (len(data['title']) > 0):
                    pa['article_title'] = data['title'][0]

                if 'volume' in data and (data['volume'] != ''):
                    pa['article_volume'] = data['volume']

                if 'author' in data and (len(data['author']) > 0):

                    fa_last_name = data['author'][0]['family']
                    fa_first_name = data['author'][0]['given']

                    pa['first_author'] = fa_last_name + ',' + fa_first_name

                    if (len(data['author']) > 1):

                        co_authors = ''
                        for a in data['author'][1:]:
                            co_authors += a['family'] + ',' + a['given'] + "; "

                        pa['co_authors'] = co_authors

                if 'issued' in data:
                    year = data['issued']['date-parts'][0][0]

                    month = 1
                    if len(data['issued']['date-parts'][0]) >= 2:
                        month = data['issued']['date-parts'][0][1]

                    day = 1
                    if len(data['issued']['date-parts'][0]) >= 3:
                        day = data['issued']['date-parts'][0][2]

                    pa['date_of_publication'] = toDateTime(month, day, year)

                if 'article_type' in data and (data['article_type'] != ''):
                    pa['article_type'] = data['article_type']

                if 'subject_category' in data and (data['subject_category'] != ''):
                    pa['subject_category'] = data['subject_category']

                if 'custom' in data and (data['custom'] != ''):
                    pa['custom'] = data['custom']

                if 'editor' in data and (data['editor'] != ''):
                    pa['editor'] = data['editor']

                if 'scopus_citation_count' in data and (data['scopus_citation_count'] != ''):
                    pa['scopus_citation_count'] = data['scopus_citation_count']
                else:
                    pa['scopus_citation_count'] = 0

                if pa.hw_metadata_retrieved is None:
                    pa.hw_metadata_retrieved = False

                pa.save()

                # Add Placeholder Citations
                for yr in range(pa.date_of_publication.year, today.year + 1):

                    plac = Article_Citations()
                    plac['publisher_id'] = publisher
                    plac['article_doi'] = pa.article_doi
                    plac['citation_doi'] = str(yr) + "-placeholder"
                    plac['updated'] = updated
                    plac['created'] = updated
                    plac['citation_date'] = datetime(yr, 1, 1)
                    plac['citation_count'] = 0
                    plac.save()

                tlogger.info("\n" + str(count-1) + ". Inserting record: " + publisher + " / " + doi)


            tsv.close()

            pu = Publisher_Vizor_Updates()
            pu['publisher_id'] = publisher
            pu['vizor_id'] = 'published_articles'
            pu['updated'] = updated
            pu.save()

            m = PublisherMetadata.filter(publisher_id=publisher).first()
            m.published_articles_last_updated = updated
            m.save()

        self.taskEnded(publisher, job_id, t0, tlogger, count)

        args = {}
        args[BaseTask.PUBLISHER_ID] = publisher
        args[BaseTask.WORK_FOLDER] = workfolder
        args[BaseTask.JOB_ID] = job_id

        return args


def toDateTime(month, day, year):

    if year < 99:
        year += 2000

    # date (y, m, d)
    date = datetime(year, month, day)
    return date








