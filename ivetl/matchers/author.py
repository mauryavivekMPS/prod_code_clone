from fuzzywuzzy import fuzz


def match_authors(rejected_last_names, crossref_last_names, tlogger=None):
    authors_match = False
    num_match = 0

    rejected_last_names.sort()
    crossref_last_names.sort()

    for a in rejected_last_names:
        for xref_a in crossref_last_names:
            if fuzz.ratio(a, xref_a) >= 80:
                num_match += 1
                break

    num_rejected = len(rejected_last_names)
    num_crossref = len(crossref_last_names)

    denom = num_rejected

    if num_rejected <= 0:
        ratio_match = 0.0
    else:
        ratio_match = num_match / denom

    author_match_score = ratio_match

    if tlogger:
        tlogger.info("Author Match Score: " + format(author_match_score, '.2f'))
        tlogger.info("Rejected Authors: " + ','.join(rejected_last_names))
        tlogger.info("CrossRef Authors: " + ','.join(crossref_last_names))

    if denom >= 5 and ratio_match >= 0.70:
        authors_match = True
    elif denom == 4 and ratio_match >= 0.75:
        authors_match = True
    elif denom == 3 and ratio_match >= 0.66:
        authors_match = True
    elif ratio_match == 1.0:
        authors_match = True

    return authors_match, author_match_score
