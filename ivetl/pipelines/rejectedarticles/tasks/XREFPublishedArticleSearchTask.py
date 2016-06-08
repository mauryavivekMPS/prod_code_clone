import csv
import codecs
import json
from datetime import timedelta
from datetime import date
from ivetl.models.IssnJournal import Issn_Journal
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.connectors import CrossrefConnector
from ivetl.matchers import match_authors, match_titles

EXCLUDED_JOURNALS = [
    "10.1002/chin",
    "10.1002/ange"
]

def is_valid_journal(doi):
    for j in EXCLUDED_JOURNALS:
        if doi.startswith(j):
            return False
    return True


def remove_disallowed_chars(s):
    return ''.join(c for c in s if ord(c) < 128 and c not in ['?', '%', '\r', '\n'])


def get_last_names(name_strings):
    unique_names = set()
    for s in name_strings:
        if s and type(s) == str:
            unique_names.update([remove_disallowed_chars(full_name.split(',')[0].strip().lower()) for full_name in s.split(';')])
    return list(unique_names)


class CrossrefArticle:

    def __init__(self):
        self.cites = 0
        self.rejectiondate = ""
        self.rejectreason = ""
        self.bpmanuscripid = ""
        self.doi = ""
        self.bptitle = ""
        self.journal = ""
        self.status = ""
        self.author_first_name = ""
        self.author_last_name = ""
        self.publishdate = ""
        self.xreftitle = ""
        self.xrefauthor_surnames = []
        self.xrefcoauthors = []
        self.authormatchscore = 0.0
        self.xreftitlescore = 0.0
        self.bpeditor = ""
        self.publisher = ""

    @property
    def first_author(self):
        return self.author_last_name + ',' + self.author_first_name

    @property
    def co_authors(self):
        return ';'.join(self.xrefcoauthors)

    def set_crossref_details(self, item, issn_journals):

        j = item

        self.doi = j['DOI']

        if len(j['title']) > 0:
            self.bptitle = remove_disallowed_chars(j['title'][0])
        else:
            self.bptitle = ""

        year = j['issued']['date-parts'][0][0]

        month = 1
        if len(j['issued']['date-parts'][0]) >= 2:
            month = j['issued']['date-parts'][0][1]

        day = 1
        if len(j['issued']['date-parts'][0]) >= 3:
            day = j['issued']['date-parts'][0][2]

        self.publishdate = str(month) + '/' + str(day) + '/' + str(year)

        issn = ""
        if 'ISSN' in j:
            issn = j['ISSN'][0]

        if issn in issn_journals:
            self.journal = issn_journals[issn][0]
            self.publisher = issn_journals[issn][1]
        else:
            if 'container-title' in j and len(j['container-title']) > 0:
                self.journal = j['container-title'][0]
            if 'publisher' in j:
                self.publisher = j['publisher']

        if 'author' in j:
            authors = j['author']
            first_author = True

            for a in authors:
                if 'given' not in a:
                    a['given'] = ''
                if 'family' not in a:
                    a['family'] = ''
                if first_author:
                    self.author_last_name = a['family']
                    if 'given' in a:
                        self.author_first_name = a['given']
                    first_author = False
                    continue

                self.xrefcoauthors.append(a['family'] + "," + a['given'])


@app.task
class XREFPublishedArticleSearchTask(Task):
    ISSN_JNL_QUERY_LIMIT = 1000000

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        file = task_args['input_file']
        total_count = task_args['count']

        target_file_name = work_folder + "/" + publisher_id + "_" + "xrefpublishedarticlesearch" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\t'
                          'MANUSCRIPT_ID\t'
                          'DATA\n')

        # build Issn Journal List
        issn_journals = {}
        for ij in Issn_Journal.objects.limit(self.ISSN_JNL_QUERY_LIMIT):
            issn_journals[ij.issn] = (ij.journal, ij.publisher)

        count = 0

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        # debug titles
        title_file = codecs.open('/tmp/%s_%s.csv' % (publisher_id, job_id), 'w', 'utf-16')
        title_csv = csv.writer(title_file)

        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                if count == 1:
                    continue  # ignore the header

                # debug titles
                # if count > 20:
                #     break

                publisher = line[0]
                manuscript_id = line[1]
                data = json.loads(line[2])

                tlogger.info("\n" + str(count-1) + ". Reading In Rejected Article: " + publisher + " / " + manuscript_id)

                date_of_rejection = data['date_of_rejection']

                title = remove_disallowed_chars(data['title'])
                if title is None or title.strip == "":
                    tlogger.info("No title, skipping record")
                    continue

                author_last_names = get_last_names([data['first_author'], data['corresponding_author'], data['co_authors']])

                # debug titles
                title_csv.writerow([
                    manuscript_id,
                    'original',
                    '',
                    data['title'],
                    ','.join(author_last_names),
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                ])

                if '-' in date_of_rejection:
                    dor_parts = date_of_rejection.split('-')
                else:
                    dor_parts = date_of_rejection.split('/')

                reject_month = int(dor_parts[0])
                reject_day = int(dor_parts[1])
                reject_year = int(dor_parts[2])

                if reject_year < 99:
                    reject_year += 2000

                reject_date = date(reject_year, reject_month, reject_day)
                publish_date = reject_date + timedelta(days=1)

                def _has_results(r):
                   return r and 'ok' in r['status'] and len(r['message']['items']) > 0

                def _add_crossref_properties_to_result(r, article):
                    r["xref_journal"] = article.journal
                    r["xref_publisher"] = article.publisher
                    r["xref_publishdate"] = article.publishdate
                    r["xref_first_author"] = article.first_author
                    r["xref_co_authors_ln_fn"] = article.co_authors
                    r["xref_title"] = article.bptitle
                    r["xref_doi"] = article.doi

                data['status'] = ''

                match_strategy = [
                    {
                        'name': 'title-only-search',
                        'include_author_in_search': False,
                        'match_author': True,
                        'match_title': True,
                        'allow_50_50_match': True,
                        'allow_10_80_match': True,
                        'strict_single_author_title_match': True,
                    },
                    {
                        'name': 'title-and-author-search',
                        'include_author_in_search': True,
                        'match_author': True,
                        'match_title': True,
                        'allow_50_50_match': True,
                        'allow_10_80_match': True,
                        'strict_single_author_title_match': True,
                    },
                ]

                crossref = CrossrefConnector(tlogger=tlogger)
                matching_result = {}
                author_score = 0.0
                title_score = 0.0

                for strategy in match_strategy:

                    if matching_result:
                        break

                    if strategy['include_author_in_search']:
                        author_param = author_last_names
                    else:
                        author_param = None

                    search_results = crossref.search_article(publish_date, title, authors=author_param)
                    if _has_results(search_results):
                        for result in search_results['message']['items']:

                            article = CrossrefArticle()
                            article.set_crossref_details(result, issn_journals)

                            if not is_valid_journal(article.doi):
                                continue

                            is_author_match = True
                            crossref_last_names = get_last_names([article.first_author, article.co_authors])
                            if strategy['match_author']:
                                is_author_match, author_score = match_authors(
                                    author_last_names,
                                    crossref_last_names,
                                    tlogger=tlogger
                                )

                            is_title_match = True
                            if strategy['match_title']:
                                is_title_match, title_score = match_titles(
                                    title,
                                    article.bptitle,
                                    tlogger=tlogger
                                )

                                if strategy['strict_single_author_title_match'] and len(author_last_names) <= 1:
                                    is_title_match = title_score >= 0.5

                            is_50_50_match = False
                            if strategy['allow_50_50_match']:
                                if author_score >= 0.5 and title_score >= 0.5:
                                    is_50_50_match = True

                            is_10_80_match = False
                            if strategy['allow_10_80_match']:
                                if author_score >= 0.1 and title_score >= 0.8:
                                    is_10_80_match = True

                            # debug titles
                            if is_author_match and is_title_match or strategy['allow_50_50_match'] and is_50_50_match:
                                match_string = 'match'
                            else:
                                match_string = 'no'

                            author_match_string = ''
                            if strategy['match_author']:
                                if is_author_match:
                                    author_match_string = 'match-author'
                                else:
                                    author_match_string = 'no-author'

                            title_match_string = ''
                            if strategy['match_title']:
                                if is_title_match:
                                    title_match_string = 'match-title'
                                else:
                                    title_match_string = 'no-title'

                            fifty_fifty_match_string = ''
                            if strategy['allow_50_50_match']:
                                if is_50_50_match:
                                    fifty_fifty_match_string = 'match-50-50'
                                else:
                                    fifty_fifty_match_string = 'no-50-50'

                            ten_eighty_match_string = ''
                            if strategy['allow_10_80_match']:
                                if is_10_80_match:
                                    ten_eighty_match_string = 'match-10-80'
                                else:
                                    ten_eighty_match_string = 'no-10-80'

                            title_csv.writerow([
                                manuscript_id,
                                strategy['name'],
                                match_string,
                                article.bptitle,
                                ','.join(crossref_last_names),
                                author_match_string,
                                author_score,
                                title_match_string,
                                title_score,
                                fifty_fifty_match_string,
                                ten_eighty_match_string,
                            ])

                            if is_author_match and is_title_match or strategy['allow_50_50_match'] and is_50_50_match or strategy['allow_10_80_match'] and is_10_80_match:
                                _add_crossref_properties_to_result(result, article)
                                matching_result = result
                                break

                if matching_result:
                    matching_result['doi_lookup_status'] = "Match found"
                    data['status'] = "Match found"
                    data['xref_score'] = matching_result["score"]
                    data['xref_doi'] = matching_result["xref_doi"]
                    data['xref_journal'] = matching_result["xref_journal"]
                    data['xref_publishdate'] = matching_result["xref_publishdate"]
                    data['xref_first_author'] = matching_result["xref_first_author"]
                    data['xref_co_authors_ln_fn'] = matching_result["xref_co_authors_ln_fn"]
                    data['xref_title'] = matching_result["xref_title"]
                    data['author_match_score'] = format(author_score, '.2f')
                    data['title_match_score'] = format(title_score, '.2f')
                    data['xref_published_publisher'] = matching_result["xref_publisher"]

                    if "ISSN" in matching_result and len(matching_result["ISSN"]) > 0:
                        data['xref_journal_issn'] = matching_result["ISSN"][0]

                else:
                    data['status'] = "No match found"

                row = """%s\t%s\t%s\n""" % (
                    publisher,
                    manuscript_id,
                    json.dumps(data)
                )

                target_file.write(row)


        target_file.close()
        title_file.close()

        self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, send_notification_email=True, notification_count=total_count)

        return {
            'input_file': target_file_name,
            'count': count,
        }
