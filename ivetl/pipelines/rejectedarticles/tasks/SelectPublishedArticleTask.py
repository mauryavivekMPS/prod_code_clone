# import csv
# import codecs
# import json
# from ivetl.pipelines.rejectedarticles.tasks.AuthorMatchCheck import AuthorMatchCheck
# from ivetl.pipelines.rejectedarticles.tasks.JournalFilterCheck import JournalFilterCheck
from ivetl.celery import app
from ivetl.pipelines.task import Task
#
#
@app.task
class SelectPublishedArticleTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        pass
#         file = task_args['input_file']
#         total_count = task_args['count']
#
#         target_file_name = work_folder + "/" + publisher_id + "_" + "selectpublishedarticle" + "_" + "target.tab"
#         target_file = codecs.open(target_file_name, 'w', 'utf-16')
#         target_file.write('PUBLISHER_ID\t'
#                           'MANUSCRIPT_ID\t'
#                           'DATA\n')
#
#         count = 0
#         self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)
#
#         # debug titles
#         title_file = open('/tmp/%s_%s.csv' % (publisher_id, job_id), 'w')
#         title_csv = csv.writer(title_file)
#
#         with codecs.open(file, encoding="utf-16") as tsv:
#             for line in csv.reader(tsv, delimiter="\t"):
#                 count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
#                 if count == 1:
#                     continue  # ignore the header
#
#                 publisher = line[0]
#                 manuscript_id = line[1]
#                 data = json.loads(line[2])
#
#                 tlogger.info("\n" + str(count-1) + ". Reading In Rejected Article: " + publisher + " / " + manuscript_id)
#
#                 # debug titles
#                 title_csv.writerow([manuscript_id, 'original', data['title'], '', '', '', data['first_author'], data['corresponding_author'], data['co_authors']])
#
#                 reason = ''
#                 notes = ''
#                 score = ''
#                 title = ''
#
#                 if data['status'] == "Match found":
#
#                     xref_search_results_json = data['xref_results']
#
#                     xref_matches = xref_search_results_json['message']['items']
#                     if 'preprint_doi' in data and data['preprint_doi'] is not None and data['preprint_doi'] != '':
#                         tlogger.info("This manuscript has a preprint doi.")
#                         xref_matches = self.filter_out_published_doi(data['preprint_doi'], xref_matches)
#
#                     xref_article = JournalFilterCheck.check(xref_matches, tlogger)
#
#                     if xref_article is not None:
#
#                         title = xref_article['xref_title']
#
#                         # Check that author last names match
#                         print("\n" + str(count-1) + ". Checking Article: " + xref_article["xref_doi"] + " / " + manuscript_id )
#                         author_match_check = AuthorMatchCheck.check(
#                             data['first_author'],
#                             data['corresponding_author'],
#                             data['co_authors'],
#                             xref_article["xref_first_author"],
#                             xref_article["xref_co_authors_ln_fn"],
#                             tlogger
#                         )
#
#                         if author_match_check.is_match is False:
#                             tlogger.info("No Match Found due to mismatching authors\n")
#                             score = author_match_check.score
#                             notes = "No Match Found due to mismatching authors"
#
#                         else:
#                             score = author_match_check.score
#
#                     if xref_article is None:
#                         tlogger.info("No match found due to journal filter check\n")
#                         notes = "No match found due to journal filter check"
#
#                     if xref_article is None or author_match_check.is_match is False:
#                         data['status'] = "No match found"
#                         reason = "No match found"
#
#                     else:
#                         tlogger.info("Match Found")
#                         reason = 'Match found'
#
#                         data['status'] = "Match found"
#                         data['xref_score'] = xref_article["score"]
#                         data['xref_doi'] = xref_article["xref_doi"]
#                         data['xref_journal'] = xref_article["xref_journal"]
#                         data['xref_publishdate'] = xref_article["xref_publishdate"]
#                         data['xref_first_author'] = xref_article["xref_first_author"]
#                         data['xref_co_authors_ln_fn'] = xref_article["xref_co_authors_ln_fn"]
#                         data['xref_title'] = xref_article["xref_title"]
#                         data['author_match_score'] = format(author_match_check.score, '.2f')
#                         data['xref_published_publisher'] = xref_article["xref_publisher"]
#
#                         if "ISSN" in xref_article and len(xref_article["ISSN"]) > 0:
#                             data['xref_journal_issn'] = xref_article["ISSN"][0]
#
#                         tlogger.info("Matched Title: " + data['xref_title'])
#                         tlogger.info("Matched Journal: " + data['xref_journal'] + "\n")
#
#                     # debug titles
#                     title_csv.writerow([manuscript_id, 'match', title, reason, score, notes, xref_article.get("xref_first_author"), '', xref_article.get("xref_co_authors_ln_fn")])
#
#                     for match in xref_matches:
#                         title_csv.writerow([manuscript_id, 'all', match.get('xref_title'), '', '', '', xref_article.get("xref_first_author"), '', xref_article.get("xref_co_authors_ln_fn")])
#
#                 row = """%s\t%s\t%s\n""" % (
#                         publisher,
#                         manuscript_id,
#                         json.dumps(data))
#
#                 target_file.write(row)
#                 target_file.flush()
#
#         # debug titles
#         title_file.close()
#
#         target_file.close()
#
#         return {
#             'input_file': target_file_name,
#             'count': count,
#         }
#
#     def filter_out_published_doi(self, published_doi, xref_matches):
#
#         filtered_xref_matches = []
#
#         for xref_match in xref_matches:
#             if published_doi != xref_match["xref_doi"]:
#                 filtered_xref_matches.append(xref_match)
#
#         return filtered_xref_matches
#
#
#
#
#
#
