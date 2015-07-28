from fuzzywuzzy import fuzz
from decimal import *

from ivetl.common import common


class AuthorMatchCheck:

    def __init__(self, is_match, score):
        self.is_match = is_match
        self.score = score

    @staticmethod
    def check(reject_first_author, reject_corresponding_author, reject_co_authors_ln_fn,
              xref_first_author, xref_co_authors_ln_fn, tlogger):

         # Check that author last names match
        authors_match = False
        num_match = 0

        rejected_manuscript_authors = ''
        if reject_first_author.strip() != '':
            rejected_manuscript_authors = reject_first_author
            if reject_corresponding_author.strip() != '' and reject_first_author != reject_corresponding_author:
                rejected_manuscript_authors = rejected_manuscript_authors + ";" + reject_corresponding_author

        if rejected_manuscript_authors == '' and reject_corresponding_author.strip() != '':
                rejected_manuscript_authors = reject_corresponding_author

        if rejected_manuscript_authors != '':
            rejected_manuscript_authors = rejected_manuscript_authors + ";" + reject_co_authors_ln_fn
        else:
            rejected_manuscript_authors = reject_co_authors_ln_fn

        rejected_manuscript_author_surnames = []
        for entry in rejected_manuscript_authors.split(';'):
            entry = entry.rsplit(',', 1)
            entry = entry[0].rsplit(' ', 1)
            if len(entry) == 2:
                if entry[1].strip() != '':
                    rejected_manuscript_author_surnames.append(entry[1].lower().strip())
            else:
                if entry[0].strip() != '':
                    rejected_manuscript_author_surnames.append(entry[0].lower().strip())

        rejected_manuscript_author_surnames_len = len(rejected_manuscript_author_surnames)

        xref_article_authors = ''
        if xref_first_author != '':
            xref_article_authors = xref_first_author

        if xref_article_authors != '':
            xref_article_authors = xref_article_authors + ";" + xref_co_authors_ln_fn
        else:
            xref_article_authors = xref_co_authors_ln_fn

        xref_article_author_surnames = []
        for entry in xref_article_authors.split(';'):
            entry = entry.rsplit(',', 1)
            entry = entry[0].rsplit(' ', 1)

            if len(entry) == 2:
                if entry[1].strip() != '':
                    xref_article_author_surnames.append(entry[1].lower().strip())
            else:
                if entry[0].strip() != '':
                    xref_article_author_surnames.append(entry[0].lower().strip())

        rejected_manuscript_author_surnames.sort()
        xref_article_author_surnames.sort()

        for a in rejected_manuscript_author_surnames:
            for xref_a in xref_article_author_surnames:

                #print(a + ", " + xref_a + " = " + str(fuzz.ratio(a, xref_a)))
                if fuzz.ratio(AuthorMatchCheck.removenonascii(a), AuthorMatchCheck.removenonascii(xref_a)) >= 80:
                    num_match += 1
                    break

        #print num_match
        #print bp_authorsurnames_len
        if rejected_manuscript_author_surnames_len <= 0:
            ratio_match = 0.0
        else:
            ratio_match = Decimal(num_match) / Decimal(rejected_manuscript_author_surnames_len)
        author_match_score = ratio_match
        tlogger.info("Author Match Score: " + format(author_match_score, '.2f'))
        tlogger.info("Rejected Authors: " + ','.join(rejected_manuscript_author_surnames))
        tlogger.info("CrossRef Authors: " + ','.join(xref_article_author_surnames))

        if rejected_manuscript_author_surnames_len >= 5 and ratio_match >= 0.80:
            authors_match = True
        elif ratio_match == 1.0:
            authors_match = True

        return AuthorMatchCheck(authors_match, author_match_score)


    @staticmethod
    def removenonascii(s):
        return "".join(i for i in s if ord(i) < 128)