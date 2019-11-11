import codecs
import csv
import json
import os

from datetime import datetime
from ivetl.celery import app
from ivetl.common import common
from ivetl.models import PublishedArticle, PublishedArticleByCohort, PublisherMetadata, ArticleCitations, PublishedArticleValues, IssnJournal, ValueMapping, ValueMappingDisplay
from ivetl.pipelines.task import Task


@app.task
class InsertPublishedArticlesIntoCassandra(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        file = task_args['input_file']
        total_count = task_args['count']

        modified_articles_file_name = os.path.join(work_folder, '%s_modifiedarticles.tab' % publisher_id)
        modified_articles_file = codecs.open(modified_articles_file_name, 'w', 'utf-8')
        modified_articles_file.write('PUBLISHER_ID\tDOI\n')

        count = 0
        today = datetime.today()
        updated = today

        product = common.PRODUCT_BY_ID[product_id]

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        # build a list of ISSN journals
        issn_journals = {}
        for ij in IssnJournal.objects.fetch_size(1000).limit(100000):
            issn_journals[ij.issn] = (ij.journal, ij.publisher)

        pm = PublisherMetadata.filter(publisher_id=publisher_id).first()

        with codecs.open(file, encoding="utf-16") as tsv:

            for line in csv.reader(tsv, delimiter="\t"):

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                if count == 1:
                    continue

                doi = common.normalizedDoi(line[1])
                data = json.loads(line[3])

                # first, add the non-overlapping values straight to the published article table
                pa = PublishedArticle()
                existing_record = PublishedArticle.objects.filter(publisher_id=publisher_id, article_doi=doi).first()

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
                    issn = data['ISSN'][0]

                    pa['article_journal_issn'] = issn

                    if issn in issn_journals:
                        pa['article_journal'] = issn_journals[issn][0]

                if 'page' in data and (data['page'] != ''):
                    pa['article_pages'] = data['page']

                if 'scopus_id' in data and (data['scopus_id'] != ''):
                    pa['article_scopus_id'] = data['scopus_id']

                if 'title' in data and (len(data['title']) > 0):
                    pa['article_title'] = data['title'][0]

                if 'volume' in data and (data['volume'] != ''):
                    pa['article_volume'] = data['volume']

                if 'author' in data and (len(data['author']) > 0):

                    first_author = data['author'][0]
                    fa_last_name = first_author.get('family', '')
                    fa_first_name = first_author.get('given', '')
                    pa['first_author'] = fa_last_name + ',' + fa_first_name

                    if len(data['author']) > 1:
                        co_authors = ''
                        for a in data['author'][1:]:

                            if 'family' in a:

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
                    pa.scopus_citation_count = data['scopus_citation_count']
                else:
                    pa.scopus_citation_count = 0

                if 'scopus_subtype' in data:
                    pa.scopus_subtype = data['scopus_subtype']

                if pa.hw_metadata_retrieved is None:
                    pa.hw_metadata_retrieved = False

                if 'mendeley_saves' in data:
                    pa.mendeley_saves = data['mendeley_saves']

                pa.altmetrics_facebook = data.get('altmetrics_facebook', None)
                pa.altmetrics_blogs = data.get('altmetrics_blogs', None)
                pa.altmetrics_twitter = data.get('altmetrics_twitter', None)
                pa.altmetrics_gplus = data.get('altmetrics_gplus', None)
                pa.altmetrics_news_outlets = data.get('altmetrics_news_outlets', None)
                pa.altmetrics_wikipedia = data.get('altmetrics_wikipedia', None)
                pa.altmetrics_video = data.get('altmetrics_video', None)
                pa.altmetrics_policy_docs = data.get('altmetrics_policy_docs', None)
                pa.altmetrics_reddit = data.get('altmetrics_reddit', None)
                pa.f1000_total_score = data.get('f1000_total_score', None)
                pa.f1000_num_recommendations = data.get('f1000_num_recommendations', None)
                pa.f1000_average_score = data.get('f1000_average_score', None)

                if product['cohort']:
                    pa.is_cohort = True
                else:
                    pa.is_cohort = False

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
                    ed_last_name = data['editor'][0].get('family', '')
                    ed_first_name = data['editor'][0].get('given', '')
                    editor = '%s, %s' % (ed_last_name, ed_first_name)

                is_open_access = 'No'
                if 'is_open_access' in data and (data['is_open_access'] != ''):
                   is_open_access = data['is_open_access']

                PublishedArticleValues.objects(article_doi=doi, publisher_id=publisher_id, source='pa', name='article_type').update(value_text=article_type)
                PublishedArticleValues.objects(article_doi=doi, publisher_id=publisher_id, source='pa', name='subject_category').update(value_text=subject_category)
                PublishedArticleValues.objects(article_doi=doi, publisher_id=publisher_id, source='pa', name='editor').update(value_text=editor)
                PublishedArticleValues.objects(article_doi=doi, publisher_id=publisher_id, source='pa', name='custom').update(value_text=custom)
                PublishedArticleValues.objects(article_doi=doi, publisher_id=publisher_id, source='pa', name='is_open_access').update(value_text=is_open_access)

                # record in cohort table
                PublishedArticleByCohort.objects.create(
                    publisher_id=publisher_id,
                    is_cohort=pa.is_cohort,
                    article_doi=pa.article_doi,
                    article_scopus_id=pa.article_scopus_id,
                    updated=updated,
                )

                # finally, add placeholder citations
                for yr in range(pa.date_of_publication.year, today.year + 1):

                    ArticleCitations.objects.create(
                        publisher_id=publisher_id,
                        article_doi=pa.article_doi,
                        citation_doi=str(yr) + "-placeholder",
                        updated=updated,
                        created=updated,
                        citation_date=datetime(yr, 1, 1),
                        citation_count=0,
                        is_cohort=pa.is_cohort,
                        citation_source_xref=True,
                        citation_source_scopus=True,
                    )

                tlogger.info(str(count-1) + ". Inserting record: " + publisher_id + " / " + doi)

                # add a record of modified files for next task
                modified_articles_file.write("%s\t%s\n" % (publisher_id, doi))
                modified_articles_file.flush()  # why is this needed?

            if product['cohort']:
                pm.cohort_articles_last_updated = updated
            else:
                pm.published_articles_last_updated = updated
            pm.save()

        modified_articles_file.close()

        task_args['input_file'] = modified_articles_file_name
        task_args['count'] = count

        return task_args


def to_date_time(month, day, year):

    if year < 99:
        year += 2000

    # date (y, m, d)
    date = datetime(year, month, day)
    return date
