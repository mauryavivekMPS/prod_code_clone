__author__ = 'nmehta, johnm'

import os
import csv
import codecs
import json
from datetime import datetime
from ivetl.celery import app
from ivetl.common.BaseTask import BaseTask
from ivetl.models import Published_Article, Publisher_Vizor_Updates, Publisher_Metadata, Article_Citations, Published_Article_Values
from ivetl.pipelines.task import Task


@app.task
class InsertPublishedArticlesIntoCassandra(Task):
    pipeline_name = "published_articles"

    def run_task(self, publisher_id, job_id, work_folder, tlogger, task_args):

        file = task_args[BaseTask.INPUT_FILE]

        modified_articles_file_name = os.path.join(work_folder, '%s_modifiedarticles.tab' % publisher_id)  # is pub_id redundant?
        modified_articles_file = codecs.open(modified_articles_file_name, 'w', 'utf-8')
        modified_articles_file.write('PUBLISHER_ID\tDOI\n')  # ..and here? we're already in a pub folder

        count = 0
        today = datetime.today()
        updated = today

        with codecs.open(file, encoding="utf-16") as tsv:

            for line in csv.reader(tsv, delimiter="\t"):

                count += 1
                if count == 1:
                    continue

                doi = line[1]
                data = json.loads(line[2])

                # first, add the non-overlapping values straight to the published article table
                pa = Published_Article()
                existing_record = Published_Article.objects.filter(publisher_id=publisher_id, article_doi=doi).first()

                if existing_record:
                    pa = existing_record
                else:
                    pa['publisher_id'] = publisher_id
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

                    fa_first_name = ''
                    if 'given' in data['author'][0]:
                        fa_first_name = data['author'][0]['given']

                    pa['first_author'] = fa_last_name + ',' + fa_first_name

                    if len(data['author']) > 1:
                        co_authors = ''
                        for a in data['author'][1:]:

                            co_authors += a['family']

                            if 'given' in a:
                                co_authors += ',' + a['given'] + "; "
                            else:
                                co_authors += "; "

                        pa['co_authors'] = co_authors

                if 'issued' in data:
                    year = data['issued']['date-parts'][0][0]

                    month = 1
                    if len(data['issued']['date-parts'][0]) >= 2:
                        month = data['issued']['date-parts'][0][1]

                    day = 1
                    if len(data['issued']['date-parts'][0]) >= 3:
                        day = data['issued']['date-parts'][0][2]

                    pa['date_of_publication'] = to_date_time(month, day, year)

                if 'is_open_access' in data and (data['is_open_access'] != ''):
                    pa['is_open_access'] = data['is_open_access']
                else:
                    pa['is_open_access'] = 'No'

                if 'scopus_citation_count' in data and (data['scopus_citation_count'] != ''):
                    pa['scopus_citation_count'] = data['scopus_citation_count']
                else:
                    pa['scopus_citation_count'] = 0

                if pa.hw_metadata_retrieved is None:
                    pa.hw_metadata_retrieved = False

                pa.save()

                # now add overlapping values to the values table, and leave the rest to the resolver
                article_type = 'None'
                if 'article_type' in data and (data['article_type'] != ''):
                    article_type = data['article_type']

                subject_category = 'None'
                if 'subject_category' in data and (data['subject_category'] != ''):
                    subject_category = data['subject_category']

                custom = None
                if 'custom' in data and (data['custom'] != ''):
                    custom = data['custom']

                editor = None
                if 'editor' in data and (data['editor'] != ''):
                    ed_last_name = data['author'][0]['family']
                    ed_first_name = ''
                    if 'given' in data['author'][0]:
                        ed_first_name = data['author'][0]['given']
                    editor = '%s, %s' % (ed_last_name, ed_first_name)

                Published_Article_Values.objects(article_doi=doi, publisher_id=publisher_id, source='pa', name='article_type').update(value_text=article_type)
                Published_Article_Values.objects(article_doi=doi, publisher_id=publisher_id, source='pa', name='subject_category').update(value_text=subject_category)
                Published_Article_Values.objects(article_doi=doi, publisher_id=publisher_id, source='pa', name='editor').update(value_text=editor)
                Published_Article_Values.objects(article_doi=doi, publisher_id=publisher_id, source='pa', name='custom').update(value_text=custom)

                # finally, add placeholder citations
                for yr in range(pa.date_of_publication.year, today.year + 1):

                    plac = Article_Citations()
                    plac['publisher_id'] = publisher_id
                    plac['article_doi'] = pa.article_doi
                    plac['citation_doi'] = str(yr) + "-placeholder"
                    plac['updated'] = updated
                    plac['created'] = updated
                    plac['citation_date'] = datetime(yr, 1, 1)
                    plac['citation_count'] = 0
                    plac.save()

                tlogger.info(str(count-1) + ". Inserting record: " + publisher_id + " / " + doi)

                # add a record of modified files for next task
                modified_articles_file.write("%s\t%s\n" % (publisher_id, doi))
                modified_articles_file.flush()  # why is this needed?

            tsv.close()

            pu = Publisher_Vizor_Updates()
            pu['publisher_id'] = publisher_id
            pu['vizor_id'] = 'published_articles'
            pu['updated'] = updated
            pu.save()

            m = Publisher_Metadata.filter(publisher_id=publisher_id).first()
            m.published_articles_last_updated = updated
            m.save()

        modified_articles_file.close()
        return {self.COUNT: count, 'modified_articles_file': modified_articles_file_name}


def to_date_time(month, day, year):

    if year < 99:
        year += 2000

    # date (y, m, d)
    date = datetime(year, month, day)
    return date








