import os
import csv
from ivetl.validators.base import BaseValidator


class JR2Validator(BaseValidator):

    def validate_files(self, files, issns=[], publisher_id=None, crossref_username=None, crossref_password=None, increment_count_func=None, second_level_validation=False):
        errors = []
        total_count = 0
        for f in files:
            file_name = os.path.basename(f)
            with open(f, 'r', encoding='ISO-8859-1') as tsv:
                count = 0
                for line in csv.reader(tsv, delimiter='\t'):
                    if line:
                        if increment_count_func:
                            count = increment_count_func(count)
                        else:
                            count += 1

                        if count == 1:
                            expected_fields = [
                                (0, 'Subscriber ID'),
                                (1, 'Institution Name'),
                                (2, 'Journal Title'),
                                (3, 'Print ISSN'),
                                (4, 'Online ISSN'),
                                (5, 'Access Denied Category'),
                            ]

                            found_unexpected_fields = False
                            for index, title in expected_fields:
                                if line[index] != title:
                                    found_unexpected_fields = True
                                    errors.append(self.format_error(file_name, 0, "Expected field %s in column %s" % (title, index + 1)))

                            if found_unexpected_fields:
                                break

                    if len(errors) > self.MAX_ERRORS:
                        break

                total_count += count

        return total_count, errors
