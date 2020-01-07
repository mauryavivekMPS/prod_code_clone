import codecs
import csv
import json

from ivetl.common import common
from ivetl.celery import app
from ivetl.models import AltmetricsSocialData, F1000SocialData
from ivetl.pipelines.task import Task


@app.task
class GetSocialMetricsTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        file = task_args['input_file']
        total_count = task_args['count']

        target_file_name = work_folder + "/" + publisher_id + "_" + "socialmetrics" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\tDOI\tISSN\tDATA\n')

        count = 0
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                if count == 1:
                    continue

                publisher_id = line[0]
                doi = common.normalizedDoi(line[1])
                issn = line[2]
                data = json.loads(line[3])

                tlogger.info(str(count-1) + ". Getting metrics for: " + doi)

                try:
                    altmetrics_data = AltmetricsSocialData.objects.get(doi=doi)
                    data['altmetrics_facebook'] = altmetrics_data.facebook
                    data['altmetrics_blogs'] = altmetrics_data.blogs
                    data['altmetrics_twitter'] = altmetrics_data.twitter
                    data['altmetrics_gplus'] = altmetrics_data.gplus
                    data['altmetrics_news_outlets'] = altmetrics_data.news_outlets
                    data['altmetrics_wikipedia'] = altmetrics_data.wikipedia
                    data['altmetrics_video'] = altmetrics_data.video
                    data['altmetrics_policy_docs'] = altmetrics_data.policy_docs
                    data['altmetrics_reddit'] = altmetrics_data.reddit
                except AltmetricsSocialData.DoesNotExist:
                    tlogger.info('No Altmetrics data for %s' % doi)

                try:
                    f1000_data = F1000SocialData.objects.get(doi=doi)
                    data['f1000_total_score'] = f1000_data.total_score
                    data['f1000_num_recommendations'] = f1000_data.num_recommendations
                    data['f1000_average_score'] = float(f1000_data.average_score)
                except F1000SocialData.DoesNotExist:
                    tlogger.info('No F1000 data for %s' % doi)

                row = """%s\t%s\t%s\t%s\n""" % (publisher_id, doi, issn, json.dumps(data))

                target_file.write(row)

        target_file.close()

        task_args['input_file'] = target_file_name
        task_args['count'] = count

        return task_args
