__author__ = 'johnm'

import csv
import codecs
from time import time
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.pipelines.customarticledata import utils
from ivetl.models import Published_Article


@app.task
class ValidateArticleDataFiles(Task):
    pipeline_name = "custom_article_data"

    def run_task(self, publisher_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']

        t0 = time()
        total_count = 0
        found_error = False

        for f in files:
            with codecs.open(f, encoding='utf-8') as tsv:  # TODO: perhaps should be codecs.open(f, encoding="utf-16") ??
                count = 0
                for line in csv.reader(tsv, delimiter='\t'):
                    if line:
                        count += 1

                        # skip header row
                        if count == 1:
                            continue

                        # check for number of fields
                        if len(line) != 7:
                            tlogger.error("\nLine %s: Incorrect number of fields, skipping other validation (%s)" % ((count - 1), f))
                            found_error = True
                            continue

                        d = utils.parse_custom_data_line(line)

                        # we need a DOI
                        if not d['doi']:
                            tlogger.error("\nLine %s: No DOI found, skipping other validation (%s)" % ((count - 1), f))
                            found_error = True
                            continue

                        # and it needs to exist in the database
                        try:
                            article = Published_Article.get(publisher_id=publisher_id, article_doi=d['doi'])
                        except Published_Article.DoesNotExist:
                            tlogger.error("\nLine %s: The DOI wasn't found in the database, skipping other validation (%s)" % ((count - 1), f))
                            found_error = True
                            continue

                total_count += count
                tsv.close()

        t1 = time()
        tlogger.info("Rows processed:   %s" % (total_count - 1))
        tlogger.info("Time taken:       " + format(t1 - t0, '.2f') + " seconds / " + format((t1 - t0) / 60, '.2f') + " minutes")

        if not found_error:
            tlogger.info("No errors found")
        else:
            tlogger.error("\n!! ERRORS FOUND !!")
            raise Exception("Validation errors in files: %s" % files)

        return {'input_files': files}
