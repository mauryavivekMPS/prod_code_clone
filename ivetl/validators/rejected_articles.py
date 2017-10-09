import os
import csv
import codecs
from ivetl.validators.base import BaseValidator
from ivetl.utils import trim_and_strip_doublequotes


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
]


class RejectedArticlesValidator(BaseValidator):

    def validate_files(self, files, issns=[], publisher_id=None, crossref_username=None, crossref_password=None, increment_count_func=None):
        errors = []
        total_count = 0

        for f in files:
            file_name = os.path.basename(f)
            try:
                with codecs.open(f, encoding='utf-8') as tsv:
                    count = 0
                    for line in csv.reader(tsv, delimiter='\t', quoting=csv.QUOTE_NONE):
                        if line:
                            if increment_count_func:
                                count = increment_count_func(count)
                            else:
                                count += 1

                            # check for number of fields
                            if len(line) < len(COLUMNS):
                                errors.append(self.format_error(file_name, count, "Incorrect number of fields (%s present, 14 required), skipping other validation" % len(line)))
                                break

                            # check header field for correct columns names
                            valid_column_headers = True
                            if count == 1:
                                for i, col in enumerate(COLUMNS):
                                    title = trim_and_strip_doublequotes(line[i])
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

                            manuscript_id = trim_and_strip_doublequotes(line[0])
                            input_data = {
                                'date_of_rejection': trim_and_strip_doublequotes(line[1]),
                                'reject_reason': trim_and_strip_doublequotes(line[2]),
                                'title': trim_and_strip_doublequotes(line[3]),
                                'first_author': trim_and_strip_doublequotes(line[4]),
                                'corresponding_author': trim_and_strip_doublequotes(line[5]),
                                'co_authors': trim_and_strip_doublequotes(line[6]),
                                'subject_category': trim_and_strip_doublequotes(line[7]),
                                'editor': trim_and_strip_doublequotes(line[8]),
                                'submitted_journal': trim_and_strip_doublequotes(line[9]),
                                'article_type': trim_and_strip_doublequotes(line[10]),
                                'keywords': trim_and_strip_doublequotes(line[11]),
                                'custom': trim_and_strip_doublequotes(line[12]),
                                'funders': trim_and_strip_doublequotes(line[13]),
                            }

                            if not manuscript_id:
                                errors.append(self.format_error(file_name, count, "No value for MANUSCRIPT_ID"))

                            if input_data['date_of_rejection'] == "":
                                errors.append(self.format_error(file_name, count, "No value for DATE_OF_REJECTION"))

                            elif not self.valid_date(input_data['date_of_rejection']):
                                errors.append(self.format_error(file_name, count, "Invalid format for DATE_OF_REJECTION %s (Valid format is MM/DD/YY)" % input_data['date_of_rejection']))

                            if input_data['reject_reason'] == "":
                                errors.append(self.format_error(file_name, count, "No value for REJECT_REASON"))

                            if input_data['title'] == "":
                                errors.append(self.format_error(file_name, count, "No have value for TITLE"))

                            if input_data['first_author'] == "" and input_data['corresponding_author'] == "" and input_data['co_authors'] == "":
                                errors.append(self.format_error(file_name, count, "No value for any of the author fields (first, corresponding, co)"))

                            if input_data['submitted_journal'] == "":
                                errors.append(self.format_error(file_name, count, "No value for SUBMITTED_JOURNAL"))

                    total_count += count

            except UnicodeDecodeError:
                errors.append(self.format_error(file_name, 0, "This file is not in UTF-8, skipping further validation"))

        return total_count, errors

    def valid_date(self, date):

        is_valid = True

        if '-' in date:
            date_parts = date.split('-')
        else:
            date_parts = date.split('/')

        if len(date_parts) != 3:
            is_valid = False
        else:
            try:
                int(date_parts[0])
                int(date_parts[1])
                int(date_parts[2])

            except ValueError:
                is_valid = False

        return is_valid
