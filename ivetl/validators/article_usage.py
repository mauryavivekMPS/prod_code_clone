import os
import re
import codecs
from ivetl.validators.base import BaseValidator


class ArticleUsageValidator(BaseValidator):

    def validate_files(self, files, issns=[], publisher_id=None, crossref_username=None, crossref_password=None, increment_count_func=None, second_level_validation=False):

        errors = []
        total_count = 0
        field_separators = '\s*\t\s*|\s*,\s*'
        headers = frozenset(['articledoi', 'usagemonth', 'type', 'usagecount'])
        
        for f in files:
            file_name = os.path.basename(f)
            try:
                with codecs.open(f, encoding='utf-8') as tsv:
                    count = 0
                    for line in tsv:
                        if not line: continue

                        if increment_count_func:
                            count = increment_count_func(count)
                        else:
                            count += 1

                        # Validate the header row field names
                        if count == 1:
                            fieldnames = frozenset([fn.lower().replace(' ','') for fn in re.split(field_separators, line.strip())])

                            if not headers <= fieldnames:
                                errors.append(self.format_error(file_name,
                                                                count - 1,
                                                                "The file must have the following header fields: ArticleDOI, Type, UsageMonth, UsageCount")
                                              )
                            continue

                        fields = re.split(field_separators, line.strip())
                        field_count = len(fields)
                            
                        # check for number of fields
                        if field_count < 4:
                            errors.append(self.format_error(file_name,
                                                            count - 1,
                                                            "Line has {} fields, when 4 are required.".format(field_count))
                                         )
                            continue

                        if len(errors) > self.MAX_ERRORS:
                            break

                    total_count += count

            except UnicodeDecodeError:
                errors.append(self.format_error(file_name, 0, "This file is not UTF-8, skipping further validation"))

        return total_count, errors
