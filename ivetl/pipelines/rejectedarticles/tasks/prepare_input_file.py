import codecs
import csv
import json

from datetime import datetime
from ivetl.common import common
from ivetl import utils
from ivetl.celery import app
from ivetl.models import RejectedArticles
from ivetl.pipelines.task import Task


@app.task
class PrepareInputFileTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        files = task_args['input_files']
        total_count = task_args['count']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        target_file_name = work_folder + "/" + publisher_id + "_" + "preparedinput" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('\t'.join(['PUBLISHER_ID', 'MANUSCRIPT_ID', 'DATA']) + '\n')

        count = 0

        for file in files:
            encoding = utils.guess_encoding(file)
            with codecs.open(file, encoding=encoding) as tsv:
                count_in_file = 0

                for line in csv.reader(tsv, delimiter="\t", quoting=csv.QUOTE_NONE):
                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                    count_in_file += 1

                    # skip header row
                    if count_in_file == 1:
                        continue

                    tlogger.info("\n" + str(count-1) + ". Reading In Rejected Article: " + line[3])

                    manuscript_id = utils.trim_and_strip_doublequotes(line[0])

                    input_data = {
                        'manuscript_id': manuscript_id,
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

                    if len(line) >= 11:
                        article_type = utils.trim_and_strip_doublequotes(line[10])
                        if article_type:
                            input_data['article_type'] = article_type

                    if len(line) >= 12:
                        keywords = utils.trim_and_strip_doublequotes(line[11])
                        if keywords:
                            input_data['keywords'] = keywords

                    if len(line) >= 13:
                        custom = utils.trim_and_strip_doublequotes(line[12])
                        if custom:
                            input_data['custom'] = custom

                    if len(line) >= 14:
                        funders = utils.trim_and_strip_doublequotes(line[13])
                        if funders:
                            input_data['funders'] = funders

                    if len(line) >= 15:
                        preprint_doi = common.normalizedDoi(utils.trim_and_strip_doublequotes(line[14]))
                        if preprint_doi:
                            input_data['preprint_doi'] = preprint_doi

                    input_data['source_file_name'] = file

                    # Perform an update if the manuscript_id is already in the DB.
                    # Blank input_data fields retain the value already in the DB.
                    try:
                        r = RejectedArticles.objects.get(publisher_id=publisher_id, manuscript_id=manuscript_id)

                        for field, val in input_data.items():
                            if val == "":
                                # r.get(field) doesn't work, can throw an exception
                                try:
                                    input_data[field] = r[field]
                                except KeyError:
                                    tlogger.info('Field "' + field + '" is not a database column')

                                # Cassandra returns dates as datetime objects.
                                if isinstance(input_data[field], datetime):
                                    # subclas json.JSONEncoder, or def a json.dumps default serializer.
                                    input_data[field] = input_data[field].strftime('%m/%d/%Y')

                    except RejectedArticles.DoesNotExist:
                        # manuscript is not in db, so nothing to do
                        pass

                    row = '\t'.join([publisher_id, manuscript_id, json.dumps(input_data)]) + '\n'
                    target_file.write(row)

        target_file.close()

        task_args['count'] = count
        task_args['input_file'] = target_file_name
        return task_args
