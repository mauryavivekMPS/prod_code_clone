import os
import csv
from ivetl.validators.base import BaseValidator
from ivetl import utils
from ivetl.models import PublisherJournal


class BundleDefinitionsValidator(BaseValidator):
    def validate_files(self, files, issns=[], publisher_id=None, crossref_username=None, crossref_password=None, increment_count_func=None, second_level_validation=False):
        errors = []

        all_publisher_issns = set()
        for journal in PublisherJournal.objects.filter(publisher_id=publisher_id):
            all_publisher_issns.add(journal.electronic_issn)
            all_publisher_issns.add(journal.print_issn)

        total_count = 0
        for f in files:
            file_name = os.path.basename(f)
            try:
                encoding = utils.guess_encoding(f)
                with open(f, encoding=encoding) as tsv:
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
                            if len(line) < 2:
                                errors.append(self.format_error(file_name, count - 1, "Incorrect number of fields, skipping other validation"))
                                continue

                            # check for valid ISSNs
                            for issn in line[1:]:
                                if issn and issn not in all_publisher_issns:
                                    errors.append(self.format_error(file_name, count - 1, "Unknown ISSN: %s" % issn))

                        if len(errors) > self.MAX_ERRORS:
                            break

                    total_count += count

            except UnicodeDecodeError:
                errors.append(self.format_error(file_name, 0, "This file is not a recognized encoding, skipping further validation"))

        return total_count, errors
