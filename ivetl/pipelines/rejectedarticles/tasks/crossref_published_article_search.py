import codecs
import csv
import json
import os
import re
import threading

from cassandra.cqlengine.query import DoesNotExist
from datetime import date
from datetime import timedelta
from ivetl.celery import app
from ivetl.common import common
from ivetl.connectors import CrossrefConnector
from ivetl.connectors import PubMedConnector
from ivetl.matchers import match_authors, match_titles
from ivetl.models.issn_journal import IssnJournal
from ivetl.models import PublisherJournal
from ivetl.models import RejectedArticleOverride
from ivetl.pipelines.task import Task

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
    return ''.join(c for c in s if ord(c) < 128 and c not in ['?', '%', '\r', '\n', '-', '~', '#'])


def remove_hex(s):
    return re.sub('&.*;', '', s)


def remove_disallowed_words(s):
    s = re.sub('(\W|^)or(\W|$)', ' ', s, flags=re.IGNORECASE)
    s = re.sub('(\W|^)and(\W|$)', ' ', s, flags=re.IGNORECASE)
    s = re.sub('(\W|^)not(\W|$)', ' ', s, flags=re.IGNORECASE)
    return s


def clean_crossref_input(s):
    if s:
        return remove_disallowed_chars(remove_disallowed_words(remove_hex(s)))
    else:
        return ''


def get_last_names(name_strings):
    unique_names = set()
    for s in name_strings:
        if s and type(s) == str:unique_names.update([full_name.split(',')[0].strip().lower()
                                                         for full_name in s.split(';')
                                                         if full_name.split(',')[0].strip()]
                                                    )
    return list(unique_names)

def has_rejected_article_override(publisher_id, manuscript_id, doi,
                                  tlogger=None):
    try:
        override = RejectedArticleOverride.objects.get(
            publisher_id=publisher_id,
            manuscript_id=manuscript_id,
            doi=doi
        )
        if override:
            return True
    except DoesNotExist:
        return False
    except Exception as inst:
        if tlogger:
            tlogger.info('Unexpected exception checking RejectedArticleOverride')
            tlogger.info(inst)
        else:
            print('Unexpected exception checking RejectedArticleOverride')
            print(inst)
    return False

def crossref_lookup(publisher, manuscript_id, data, issn_journals, tlogger,
                    mutex, target_file, matcher_debug_csv, pub_journals):
    date_of_rejection = data['date_of_rejection']

    title = clean_crossref_input(data['title'])
    if title is None or not title.strip():
        tlogger.info("No title, skipping record")
        return

    tlogger.info('first: %s' % data['first_author'])
    tlogger.info('corresponding_author: %s' % data['corresponding_author'])
    tlogger.info('co_authors: %s' % data['co_authors'])

    author_last_names = get_last_names([
        clean_crossref_input(data['first_author']),
        clean_crossref_input(data['corresponding_author']),
        clean_crossref_input(data['co_authors'])
    ])

    tlogger.info('author_last_names: %s' % author_last_names)

    if not author_last_names:
        tlogger.info('No authors, skipping record')
        return

    # Date must be MM/DD/YYYY USA format.
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

    use_pubmed_override = False
    submitted_journal = data['submitted_journal']
    if submitted_journal in pub_journals:
        use_pubmed_override = pub_journals[submitted_journal][0]

    def _has_results(r):
        return r and 'ok' in r['status'] and len(r['message']['items']) > 0

    def _add_crossref_properties_to_result(r, a):
        r["xref_journal"] = a.journal
        r["xref_publisher"] = a.publisher
        r["xref_publishdate"] = a.publishdate
        r["xref_first_author"] = a.first_author
        r["xref_co_authors_ln_fn"] = a.co_authors
        r["xref_title"] = a.bptitle
        r["xref_doi"] = common.normalizedDoi(a.doi)

    data['status'] = ''

    match_strategy = [
        {
            'name': 'generic-query-search',
            'use_generic_query_param': True,
            'include_author_in_search': False,
            'match_author': True,
            'match_title': True,
            'allow_50_50_match': True,
            'allow_10_80_match': True,
            'strict_single_author_title_match': True,
            'easy_title_match_on_perfect_author': True,
        },
        {
            'name': 'title-only-search',
            'use_generic_query_param': False,
            'include_author_in_search': False,
            'match_author': True,
            'match_title': True,
            'allow_50_50_match': True,
            'allow_10_80_match': True,
            'strict_single_author_title_match': True,
            'easy_title_match_on_perfect_author': True,
        },
        {
            'name': 'title-and-author-search',
            'use_generic_query_param': False,
            'include_author_in_search': True,
            'match_author': True,
            'match_title': True,
            'allow_50_50_match': True,
            'allow_10_80_match': True,
            'strict_single_author_title_match': True,
            'easy_title_match_on_perfect_author': True,
        },
    ]

    crossref = CrossrefConnector(tlogger=tlogger)
    pubmed = PubMedConnector(tlogger=tlogger)
    matching_result = {}
    author_score = 0.0
    title_score = 0.0
    new_title_score = 0.0
    strict_match = False
    easy_match = False

    for strategy in match_strategy:

        if matching_result:
            break

        if strategy['include_author_in_search']:
            author_param = author_last_names
        else:
            author_param = None

        search_results = crossref.search_article(
            publish_date,
            title,
            authors=author_param,
            use_generic_query_param=strategy['use_generic_query_param']
        )

        if _has_results(search_results):
            for result in search_results['message']['items']:

                article = CrossrefArticle()
                article.set_crossref_details(result, issn_journals)

                if not is_valid_journal(article.doi):
                    continue

                if has_rejected_article_override(publisher_id=publisher,
                    manuscript_id=manuscript_id, doi=article.doi,
                    tlogger=tlogger):
                    continue

                if use_pubmed_override and pubmed.override(result):
                    continue

                is_author_match = True
                crossref_last_names = get_last_names(
                    [article.first_author, article.co_authors])
                if strategy['match_author']:
                    with mutex:
                        is_author_match, author_score = match_authors(
                            author_last_names,
                            crossref_last_names,
                        tlogger=tlogger
                        )

                is_title_match = True
                if strategy['match_title']:
                    with mutex:
                        is_title_match, title_score, new_title_score = match_titles(
                            title,
                            article.bptitle,
                            tlogger=tlogger
                            )

                    if strategy['strict_single_author_title_match'] and len(author_last_names) <= 1:
                        is_title_match = title_score >= 0.5
                        if is_title_match:
                            strict_match = True

                    if strategy['easy_title_match_on_perfect_author'] and len(author_last_names) >= 3 and author_score >= 1.0:
                        is_title_match = title_score >= 0.14
                        if is_title_match:
                            easy_match = True

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

                with mutex:
                    matcher_debug_csv.writerow([
                        manuscript_id,
                        strategy['name'],
                        match_string,
                        data['title'],
                        article.bptitle,
                        ','.join(author_last_names),
                        ','.join(crossref_last_names),
                        author_match_string,
                        author_score,
                        title_match_string,
                        title_score,
                        fifty_fifty_match_string,
                        ten_eighty_match_string,
                        new_title_score,
                        'strict' if strict_match else 'no',
                        'easy' if easy_match else 'no',
                        ])

                if is_author_match and is_title_match or strategy['allow_50_50_match'] and is_50_50_match or strategy['allow_10_80_match'] and is_10_80_match:
                    _add_crossref_properties_to_result(result, article)
                    matching_result = result
                    break

    if matching_result:
        matching_result['doi_lookup_status'] = "Match found"
        data['status'] = "Match found"
        data['xref_score'] = matching_result["score"]
        data['xref_doi'] = common.normalizedDoi(matching_result["xref_doi"])
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

    with mutex:
        target_file.write(row)

    return


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
        self.use_pubmed_override = False

    @property
    def first_author(self):
        return self.author_last_name + ',' + self.author_first_name

    @property
    def co_authors(self):
        return ';'.join(self.xrefcoauthors)

    def set_crossref_details(self, item, issn_journals):

        j = item

        self.doi = common.normalizedDoi(j['DOI'])

        if len(j['title']) > 0:
            self.bptitle = j['title'][0]
        else:
            self.bptitle = ""

        if 'published-online' in j:

            year = j['published-online']['date-parts'][0][0]

            month = 1
            if len(j['published-online']['date-parts'][0]) >= 2:
                month = j['published-online']['date-parts'][0][1]

            day = 1
            if len(j['published-online']['date-parts'][0]) >= 3:
                day = j['published-online']['date-parts'][0][2]
        else:
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

        running = {}
        concurrency = 10
        mutex = threading.Lock()

        target_file_name = work_folder + "/" + publisher_id + \
            "_" + "xrefpublishedarticlesearch" + "_" + "target.tab"

        already_processed = set()

        # if the file exists, read it in assuming a job restart
        if os.path.isfile(target_file_name):
            with codecs.open(target_file_name, encoding='utf-16') as tsv:
                for line in csv.reader(tsv, delimiter='\t'):
                    if line and len(line) == 3 and line[0] != 'PUBLISHER_ID':
                        manuscript_id = line[1]
                        already_processed.add(manuscript_id)

        if already_processed:
            tlogger.info('Found %s existing items to reuse' %
                         len(already_processed))

        target_file = codecs.open(target_file_name, 'a', 'utf-16')

        if not already_processed:
            target_file.write('\t'.join(['PUBLISHER_ID', 'MANUSCRIPT_ID', 'DATA']) + '\n')

        # build Issn Journal List
        issn_journals = {}
        for ij in IssnJournal.objects.fetch_size(1000).limit(self.ISSN_JNL_QUERY_LIMIT):
            ijvalue = (ij.journal, ij.publisher)
            issn_journals[ij.issn] = ijvalue

        # build Publisher Journal List
        pub_journals = {}
        for pj in PublisherJournal.objects.filter(publisher_id=publisher_id):
            pjvalue = (pj.use_pubmed_override,)
            issn = pj.print_issn
            eissn = pj.electronic_issn
            if eissn in issn_journals:
                pjtitle = issn_journals[eissn][0]
                pub_journals[pjtitle] = pjvalue
            elif issn in issn_journals:
                pjtitle = issn_journals[eissn][0]
                pub_journals[pjtitle] = pjvalue

        count = 0

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        # debug titles
        matcher_debug_file = codecs.open(os.path.join(
            common.TMP_DIR, '%s_%s.csv' % (publisher_id, job_id)), 'w', 'utf-16')
        matcher_debug_csv = csv.writer(matcher_debug_file)

        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                if count == 1:
                    continue  # ignore the header

                publisher = line[0]
                manuscript_id = line[1]
                data = json.loads(line[2])

                if manuscript_id in already_processed:
                    continue

                tlogger.info("\n" + str(count-1) + ". Reading In Rejected Article: " +
                             publisher + " / " + manuscript_id)

                tid = (count-1) % concurrency
                if tid in running:
                    running[tid].join()

                running[tid] = threading.Thread(
                                target=crossref_lookup, args=(
                                    publisher, manuscript_id, data,
                                    issn_journals, tlogger,
                                    mutex, target_file, matcher_debug_csv,
                                    pub_journals)
                    )

                running[tid].start()

        for tid in running:
            running[tid].join()

        target_file.close()
        matcher_debug_file.close()

        task_args['count'] = count
        task_args['input_file'] = target_file_name
        return task_args
