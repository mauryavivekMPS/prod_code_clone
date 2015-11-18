import os
import csv
import codecs
from ivetl.validators.base import BaseValidator


class RejectedArticlesValidator(BaseValidator):
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
                            if len(line) != 10:
                                errors.append("%s : %s - Incorrect number of fields, skipping other validation" % (file_name, (count - 1)))
                                continue

                            input_data = {}
                            input_data['manuscript_id'] = line[0].strip()
                            input_data['date_of_rejection'] = line[1].strip()
                            input_data['reject_reason'] = line[2].strip()
                            input_data['title'] = line[3].strip()
                            input_data['first_author'] = line[4].strip()
                            input_data['corresponding_author'] = line[5].strip()
                            input_data['co_authors'] = line[6].strip()
                            input_data['subject_category'] = line[7].strip()
                            input_data['editor'] = line[8].strip()
                            input_data['submitted_journal'] = line[9].strip()
                            input_data['article_type'] = ''
                            input_data['keywords'] = ''
                            input_data['custom'] = ''
                            input_data['funders'] = ''

                            if len(line) >= 11 and line[10].strip() != '':
                                input_data['article_type'] = line[10].strip()

                            if len(line) >= 12 and line[11].strip() != '':
                                input_data['keywords'] = line[11].strip()

                            if len(line) >= 13 and line[12].strip() != '':
                                input_data['custom'] = line[12].strip()

                            if len(line) >= 14 and line[13].strip() != '':
                                input_data['funders'] = line[13].strip()

                            if len(line) >= 15 and line[14].strip() != '':
                                input_data['published_doi'] = line[14].strip()

                            if input_data['manuscript_id'] == "":
                                errors.append("%s : %s - Does not have value for MANUSCRIPT_ID" % (file_name, (count - 1)))

                            if input_data['date_of_rejection'] == "":
                                errors.append("%s : %s - Does not have value for DATE_OF_REJECTION" % (file_name, (count - 1)))

                            elif not self.valid_date(input_data['date_of_rejection']):
                                errors.append("%s : %s - Does not have value for DATE_OF_REJECTION" % (file_name, (count - 1)))

                            if input_data['reject_reason'] == "":
                                errors.append("%s : %s - Does not have value for REJECT_REASON" % (file_name, (count - 1)))

                            if input_data['title'] == "":
                                errors.append("%s : %s - Does not have value for TITLE" % (file_name, (count - 1)))

                            if input_data['first_author'] == "" and input_data['corresponding_author'] == "" and input_data['co_authors'] == "":
                                errors.append("%s : %s - Does not have value for any of the author fields (first, corresponding, co)" % (file_name, (count - 1)))

                            if input_data['submitted_journal'] == "":
                                errors.append("%s : %s - Does not have value for SUBMITTED_JOURNAL" % (file_name, (count - 1)))

                    total_count += count

            except UnicodeDecodeError:
                errors.append("%s : %s - This file is not UTF-8, skipping further validation" % (file_name, 0))

        return total_count, errors

    def valid_date(self, date):

        is_valid = True

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
