import csv
import codecs
import random
from ivetl.connectors.crossref import CrossrefConnector
import datetime
import re


def remove_hex(s):
    return re.sub('&.*;', '', s)


def remove_disallowed_words(s):
    s = re.sub('(\W|^)or(\W|$)', ' ', s, flags=re.IGNORECASE)
    s = re.sub('(\W|^)and(\W|$)', ' ', s, flags=re.IGNORECASE)
    s = re.sub('(\W|^)not(\W|$)', ' ', s, flags=re.IGNORECASE)
    return s


def remove_disallowed_chars(s):
    return ''.join(c for c in s if ord(c) < 128 and c not in ['?', '%', '\r', '\n', '-', '~', '#'])


def clean_crossref_input(s):
    if s:
        return remove_disallowed_chars(remove_disallowed_words(remove_hex(s)))
    else:
        return ''


def main():

    input_filename = "./ONG_20102016titletocforratmatch"
    output_filename = input_filename + "_with_doi"

    out_file = codecs.open(output_filename + ".tsv", 'w', 'utf-8')
    out_file.write('DOI\t'
                   'TITLE\t'
                   'ARTICLE_TYPE\n')

    crossref = CrossrefConnector(tlogger=None)
    publish_date = datetime.date(2010, 1, 1)

    with open(input_filename + '.tsv', 'r', encoding='utf-8') as tsv:

        reader = csv.reader(tsv, delimiter="\t")
        next(reader)
        count = 0

        for line in reader:
            count += 1

            title = line[4]
            article_type = line[8]

            print(str(count) + ". Searching for title: " + title + "/" + article_type)
            search_results = crossref.search_article(
                publish_date,
                clean_crossref_input(title).replace('&', ' '),
                use_generic_query_param=True
            )

            for result in search_results['message']['items']:
                if 'Ovid' in result['publisher']:
                    doi = result['DOI']
                    break

            print(str(count) + ". DOI: " + doi)
            print()

            row = """%s\t%s\t%s\n""" % (doi, title, article_type)

            out_file.write(row)

    out_file.close()


if __name__ == "__main__":
    main()


