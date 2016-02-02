import os
import csv
import codecs
from ivetl.validators.base import BaseValidator


class ArticleUsageValidator(BaseValidator):
    def validate_files(self, files, publisher_id, increment_count_func=None):

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
                            if len(line) != 42:
                                errors.append(self.format_error(file_name, count - 1, "Incorrect number of fields, skipping other validation"))
                                continue

                    total_count += count

            except UnicodeDecodeError:
                errors.append(self.format_error(file_name, 0, "This file is not UTF-8, skipping further validation"))

        return total_count, errors
