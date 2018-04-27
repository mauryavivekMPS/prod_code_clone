import os
import csv
from ivetl.validators.base import BaseValidator


class MetaPredictionsValidator(BaseValidator):
    def validate_files(self, files, issns=[], publisher_id=None, crossref_username=None, crossref_password=None, increment_count_func=None, second_level_validation=False):
        errors = []
        total_count = 0
        for f in files:
            file_name = os.path.basename(f)
            try:
                with open(f, encoding='utf-8') as tsv:
                    count = 0
                    for line in csv.DictReader(tsv, delimiter='\t'):
                        if line:
                            if increment_count_func:
                                count = increment_count_func(count)
                            else:
                                count += 1

                            if not line['doi']:
                                errors.append(self.format_error(file_name, count - 1, "Missing DOI, skipping other validation"))
                                continue

                        if len(errors) > self.MAX_ERRORS:
                            break

                    total_count += count

            except UnicodeDecodeError:
                errors.append(self.format_error(file_name, 0, "This file is not UTF-8, skipping further validation"))

        return total_count, errors
