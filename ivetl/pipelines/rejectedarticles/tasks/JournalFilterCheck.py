# journalsToExclude = [
#     "10.1002/chin",
#     "10.1002/ange"
# ]
#
# def is_(xref_search_results_json, tlogger):
#
#     result = None
#
#     for xref_article in xref_search_results_json:
#
#         if xref_article["doi_lookup_status"] == "No match found":
#             continue
#
#         doi = xref_article["xref_doi"]
#         exclude = False
#
#         for j in journalsToExclude:
#             if doi.startswith(j):
#                 exclude = True
#                 tlogger.info("Excluding xref article due to journal: " + doi + " // " + xref_article["xref_journal"])
#                 break
#
#         if exclude is False:
#             result = xref_article
#             break
#
#     return result
