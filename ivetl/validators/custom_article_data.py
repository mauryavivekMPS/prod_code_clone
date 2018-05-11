import os
import csv
import codecs
from ivetl.validators.base import BaseValidator
from ivetl.connectors import CrossrefConnector
from ivetl import utils

COLUMNS = [
    'DOI',
    'TOC_SECTION',
    'COLLECTION',
    'EDITOR',
    'CUSTOM',
    'CUSTOM_2',
    'CUSTOM_3',
    'CITEABLE_ARTICLE',
    'IS_OPEN_ACCESS',
]


class CustomArticleDataValidator(BaseValidator):
    
    def validate_files(self, files, issns=[], publisher_id=None, crossref_username=None, crossref_password=None, increment_count_func=None, second_level_validation=False):

        # create a crossref connector
        crossref = CrossrefConnector(crossref_username, crossref_password)

        check_first_n_records = 10

        errors = []
        total_count = 0
        for f in files:
            file_name = os.path.basename(f)
            try:
                encoding = utils.guess_encoding(f)
                with codecs.open(f, encoding=encoding) as tsv:
                    count = 0
                    for line in csv.reader(tsv, delimiter='\t'):
                        if line:
                            if increment_count_func:
                                count = increment_count_func(count)
                            else:
                                count += 1

                            # check for number of fields
                            if len(line) < len(COLUMNS):
                                errors.append(self.format_error(file_name, count, "Incorrect number of fields (%s present, %s required), skipping other validation" % (len(line), len(COLUMNS))))
                                break

                            # check header field for correct columns names
                            valid_column_headers = True
                            if count == 1:
                                for i, col in enumerate(COLUMNS):
                                    title = utils.trim_and_strip_doublequotes(line[i])
                                    if title.upper() != COLUMNS[i]:
                                        errors.append(self.format_error(file_name, count, 'Invalid column header, looking for "%s" but found "%s".' % (COLUMNS[i], title)))

                                # abandon file if the column headers are wrong
                                if valid_column_headers:
                                    continue
                                else:
                                    break

                            d = {
                                'doi': line[0].strip(),
                                'toc_section': line[1].strip().title(),
                                'collection': line[2].strip().title(),
                                'editor': line[3].strip(),
                                'custom': line[4].strip(),
                                'custom_2': line[5].strip(),
                                'custom_3': line[6].strip(),
                                'is_open_access': line[8].strip(),
                            }

                            # we need a DOI
                            if not d['doi']:
                                errors.append(self.format_error(file_name, count, "No DOI found, skipping other validation"))
                                continue

                            # check for a boolean in is_open_access
                            if d['is_open_access'] and d['is_open_access'].lower() not in ('yes', 'no'):
                                errors.append(self.format_error(file_name, count, 'The is_open_access column should be "Yes", "No", or blank.'))
                                continue

                            # check that the articles are for the right publisher
                            if count <= check_first_n_records or second_level_validation:
                                article = crossref.get_article(d['doi'])

                                if not article:
                                    errors.append(self.format_error(file_name, count, "DOI not found in crossref"))
                                    continue

                                # Commenting out due to an Cell having changed ISSNs
                                # if not article['journal_issn'] in issns:
                                #     errors.append(self.format_error(file_name, count, "ISSN for DOI does not match publisher : %s : %s" % (article['journal_issn'], issns)))
                                #     continue

                        if len(errors) > self.MAX_ERRORS:
                            break

                    total_count += count - 1

            except UnicodeDecodeError:
                errors.append(self.format_error(file_name, 0, "This file is not a recognized encoding, skipping further validation"))

        return total_count, errors
