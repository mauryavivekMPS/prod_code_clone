import os
import csv
import codecs
from ivetl.pipelines.customarticledata import utils
from ivetl.models import Published_Article
from ivetl.validators.base import BaseValidator


class CustomArticleDataValidator(BaseValidator):
    def validate_files(self, files, publisher_id):
        errors = []
        total_count = 0
        for f in files:
            file_name = os.path.basename(f)
            with codecs.open(f, encoding='utf-8') as tsv:
                count = 0
                for line in csv.reader(tsv, delimiter='\t'):
                    if line:
                        count += 1

                        # skip header row
                        if count == 1:
                            continue

                        # check for number of fields
                        if len(line) != 7:
                            errors.append("%s : %s - Incorrect number of fields, skipping other validation" % (file_name, (count - 1)))
                            continue

                        d = utils.parse_custom_data_line(line)

                        # we need a DOI
                        if not d['doi']:
                            errors.append("%s : %s - No DOI found, skipping other validation" % (file_name, (count - 1)))
                            continue

                        # and it needs to exist in the database
                        try:
                            article = Published_Article.get(publisher_id=publisher_id, article_doi=d['doi'])
                        except Published_Article.DoesNotExist:
                            errors.append("%s : %s - DOI not in database, skipping other validation" % (file_name, (count - 1)))
                            continue

                total_count += count
                tsv.close()

        return total_count, errors
