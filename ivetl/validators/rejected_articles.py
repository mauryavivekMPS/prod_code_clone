import os
import csv
from datetime import datetime
import codecs
from ivetl.validators.base import BaseValidator
from ivetl import utils

COLUMNS = [
    'MANUSCRIPT_ID',
    'DATE_OF_REJECTION',
    'REJECT_REASON',
    'TITLE',
    'FIRST_AUTHOR',
    'CORRESPONDING_AUTHOR',
    'CO_AUTHORS',
    'SUBJECT_CATEGORY',
    'EDITOR',
    'SUBMITTED_JOURNAL',
    'ARTICLE_TYPE',
    'KEYWORDS',
    'CUSTOM',
    'FUNDERS',
    'CUSTOM_2',
    'CUSTOM_3',
]


class RejectedArticlesValidator(BaseValidator):

    def validate_files(self, files, issns=[], publisher_id=None, crossref_username=None, crossref_password=None, increment_count_func=None, second_level_validation=False):
        errors = []
        total_count = 0

        for f in files:
            file_name = os.path.basename(f)
            try:
                encoding = utils.guess_encoding(f)
                with codecs.open(f, encoding=encoding) as tsv:
                    count = 0
                    for line in csv.reader(tsv, delimiter='\t', quoting=csv.QUOTE_NONE):
                        if line:
                            if increment_count_func:
                                count = increment_count_func(count)
                            else:
                                count += 1

                            # check for number of fields
                            if len(line) < len(COLUMNS):
                                errors.append(self.format_error(file_name, count, "Incorrect number of fields (%s present, 16 required), skipping other validation" % len(line)))
                                break

                            # check header field for correct columns names
                            valid_column_headers = True
                            if count == 1:
                                for i, col in enumerate(COLUMNS):
                                    title = utils.trim_and_strip_doublequotes(line[i])
                                    if title.upper() != COLUMNS[i]:
                                        errors.append(self.format_error(file_name, count, 'Invalid column header, looking for "%s" but found "%s".'  % (COLUMNS[i], title)))

                                # abandon file if the column headers are wrong
                                if valid_column_headers:
                                    continue
                                else:
                                    break

                            # check for fields with just double quotes, indicating that there is probably tabs inside fields
                            for field in line:
                                if field == '"':
                                    errors.append(self.format_error(file_name, count, "Invalid format, at least one field with only a double quotation mark character"))

                            manuscript_id = utils.trim_and_strip_doublequotes(line[0])
                            input_data = {
                                'date_of_rejection': utils.trim_and_strip_doublequotes(line[1]),
                                'reject_reason': utils.trim_and_strip_doublequotes(line[2]),
                                'title': utils.trim_and_strip_doublequotes(line[3]),
                                'first_author': utils.trim_and_strip_doublequotes(line[4]),
                                'corresponding_author': utils.trim_and_strip_doublequotes(line[5]),
                                'co_authors': utils.trim_and_strip_doublequotes(line[6]),
                                'subject_category': utils.trim_and_strip_doublequotes(line[7]),
                                'editor': utils.trim_and_strip_doublequotes(line[8]),
                                'submitted_journal': utils.trim_and_strip_doublequotes(line[9]),
                                'article_type': utils.trim_and_strip_doublequotes(line[10]),
                                'keywords': utils.trim_and_strip_doublequotes(line[11]),
                                'custom': utils.trim_and_strip_doublequotes(line[12]),
                                'funders': utils.trim_and_strip_doublequotes(line[13]),
                                'custom_2': utils.trim_and_strip_doublequotes(line[14]),
                                'custom_3': utils.trim_and_strip_doublequotes(line[15]),
                            }

                            if not manuscript_id:
                                errors.append(self.format_error(file_name, count, "No value for MANUSCRIPT_ID"))

                            if input_data['date_of_rejection'] != "" and not self.valid_date(input_data['date_of_rejection']):
                                errors.append(self.format_error(file_name, count, "DATE_OF_REJECTION %s is not in the required MM/DD/YY format." % input_data['date_of_rejection']))

                        if len(errors) > self.MAX_ERRORS:
                            break

                    total_count += count

            except UnicodeDecodeError as e:
                errors.append(self.format_error(file_name, 0,
                                                'File encoding "%s" is not supported. Skipping further validation.' % e.args[0])
                                  )

        return total_count, errors

    def valid_date(self, date):
        for fmt in ('%m/%d/%y', '%m/%d/%Y', '%m-%d-%y', '%m-%d-%Y'):
            try:
               datetime.strptime(date, fmt)
               return True
            except ValueError:
                continue

            return False

