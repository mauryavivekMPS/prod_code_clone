import csv
import codecs
import json
from datetime import timedelta
from datetime import date
from ivetl.pipelines.rejectedarticles.tasks.CRArticle import CRArticle
from ivetl.models.IssnJournal import Issn_Journal
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.connectors import CrossrefConnector


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

        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                if count == 1:
                    continue  # ignore the header

                publisher = line[0]
                manuscript_id = line[1]
                data = json.loads(line[2])

                tlogger.info("\n" + str(count-1) + ". Reading In Rejected Article: " + publisher + " / " + manuscript_id)

                date_of_rejection = data['date_of_rejection']

                title = data['title']
                if title is None or title.strip == "":
                    tlogger.info("No title, skipping record")
                    continue

                def _get_last_names(s):
                    if s and type(s) == str:
                        return [full_name.split(',')[0].strip() for full_name in s.split(';')]

                author_last_names = []
                author_last_names.extend(_get_last_names(data['first_author']))
                author_last_names.extend(_get_last_names(data['corresponding_author']))
                author_last_names.extend(_get_last_names(data['co_authors']))

                if '-' in date_of_rejection:
                    dor_parts = date_of_rejection.split('-')
                else:
                    dor_parts = date_of_rejection.split('/')

                dor_month = int(dor_parts[0])
                dor_day = int(dor_parts[1])
                dor_year = int(dor_parts[2])

                if dor_year < 99:
                    dor_year += 2000

                dor_date = date(dor_year, dor_month, dor_day)
                dop_date = dor_date + timedelta(days=1)

                data['status'] = ''

                crossref = CrossrefConnector(tlogger=tlogger)
                search_results = crossref.search_article(dop_date, title, author_last_names)

                if search_results and 'ok' in search_results['status'] and len(search_results['message']['items']) > 0:
                    data['status'] = "Match found"

                    for i in search_results['message']['items']:

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

                    data['xref_results'] = search_results

                else:
                    data['status'] = "No match found"

                row = """%s\t%s\t%s\n""" % (
                    publisher,
                    manuscript_id,
                    json.dumps(data)
                )

                target_file.write(row)
                target_file.flush()

        target_file.close()

        return {
            'input_file': target_file_name,
            'count': count,
        }
