import os
import csv
import codecs
from ivetl.validators.base import BaseValidator


class CustomArticleDataValidator(BaseValidator):
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
                            if len(line) != 8:
                                errors.append("%s : %s - Incorrect number of fields, skipping other validation" % (file_name, (count - 1)))
                                continue

                            d = {
                                'doi': line[0].strip(),
                                'toc_section': line[1].strip(),
                                'collection': line[2].strip(),
                                'editor': line[3].strip(),
                                'custom': line[4].strip(),
                                'custom_2': line[5].strip(),
                                'custom_3': line[6].strip()
                            }

                            # we need a DOI
                            if not d['doi']:
                                errors.append("%s : %s - No DOI found, skipping other validation" % (file_name, (count - 1)))
                                continue

                            # and it needs to exist in the database
                            # try:
                            #     article = Published_Article.get(publisher_id=publisher_id, article_doi=d['doi'].lower())
                            # except Published_Article.DoesNotExist:
                            #     errors.append("%s : %s - DOI not in database, skipping other validation - %s" % (file_name, (count - 1), d['doi'].lower()))
                            #     continue

                    total_count += count

            except UnicodeDecodeError:
                errors.append("%s : %s - This file is not UTF-8, skipping further validation" % (file_name, 0))

        return total_count, errors
