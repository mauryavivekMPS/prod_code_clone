import os
import csv
import codecs
from ivetl.validators.base import BaseValidator
from ivetl.connectors import CrossrefConnector
from ivetl import utils


class CustomArticleDataValidator(BaseValidator):
    
    def validate_files(self, files, issns=[], publisher_id=None, crossref_username=None, crossref_password=None, increment_count_func=None):

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

                            # skip header row
                            if count == 1:
                                continue

                            # check for number of fields
                            if len(line) != 7:
                                errors.append(self.format_error(file_name, count, "Incorrect number of fields (%s present, 7 required), skipping other validation" % len(line)))
                                continue

                            d = {
                                'doi': line[0].strip(),
                                'toc_section': line[1].strip().title(),
                                'collection': line[2].strip().title(),
                                'editor': line[3].strip(),
                                'custom': line[4].strip(),
                                'custom_2': line[5].strip(),
                                'custom_3': line[6].strip()
                            }

                            # we need a DOI
                            if not d['doi']:
                                errors.append(self.format_error(file_name, count, "No DOI found, skipping other validation"))
                                continue

                            # check that the articles are for the right publisher
                            if count <= check_first_n_records:
                                article = crossref.get_article(d['doi'])

                                if not article:
                                    errors.append(self.format_error(file_name, count - 1, "DOI not found in crossref"))
                                    continue

                                # Commenting out due to an Cell having changed ISSNs
                                # if not article['journal_issn'] in issns:
                                #     errors.append(self.format_error(file_name, count - 1, "ISSN for DOI does not match publisher : %s : %s" % (article['journal_issn'], issns)))
                                #     continue

                    total_count += count-1

            except UnicodeDecodeError:
                errors.append(self.format_error(file_name, 0, "This file is not UTF-8, skipping further validation"))

        return total_count, errors
