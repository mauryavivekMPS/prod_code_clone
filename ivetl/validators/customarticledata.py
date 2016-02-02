import os
import csv
import codecs
from ivetl.validators.base import BaseValidator
from ivetl.models import Publisher_Metadata, Publisher_Journal
from ivetl.connectors import CrossrefConnector


class CustomArticleDataValidator(BaseValidator):
    def validate_files(self, files, publisher_id, increment_count_func=None):

        # get all valid ISSNs for publisher
        all_issns = []
        for j in Publisher_Journal.objects.filter(publisher_id=publisher_id, product_id='published_articles'):
            all_issns.append(j.electronic_issn)
            all_issns.append(j.print_issn)

        # create a crossref connector
        publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)
        crossref = CrossrefConnector(publisher.crossref_username, publisher.crossref_password)

        check_first_n_records = 10

        errors = []
        total_count = 0
        for f in files:
            file_name = os.path.basename(f)
            try:
                with codecs.open(f, encoding='utf-8') as tsv:
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
                            if len(line) != 8:
                                errors.append(self.format_error(file_name, count - 1, "Incorrect number of fields, skipping other validation"))
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
                                errors.append(self.format_error(file_name, count - 1, "No DOI found, skipping other validation"))
                                continue

                            # check that the articles are for the right publisher
                            if count <= check_first_n_records:
                                article = crossref.get_article(d['doi'])

                                if not article['journal_issn'] in all_issns:
                                    errors.append(self.format_error(file_name, count - 1, "ISSN for DOI does not match publisher"))
                                    continue

                    total_count += count

            except UnicodeDecodeError:
                errors.append(self.format_error(file_name, 0, "This file is not UTF-8, skipping further validation"))

        return total_count, errors
