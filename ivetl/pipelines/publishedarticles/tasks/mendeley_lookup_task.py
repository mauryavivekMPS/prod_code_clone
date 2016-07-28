import csv
import codecs
import json
from ivetl.common import common
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.connectors import MendeleyConnector
from ivetl.alerts import run_alerts, send_alert_notifications
from ivetl.models import PublishedArticle


@app.task
class MendeleyLookupTask(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        file = task_args['input_file']
        total_count = task_args['count']

        target_file_name = work_folder + "/" + publisher_id + "_" + "mendeleylookup" + "_" + "target.tab"
        target_file = codecs.open(target_file_name, 'w', 'utf-16')
        target_file.write('PUBLISHER_ID\tDOI\tISSN\tDATA\n')

        mendeley = MendeleyConnector(common.MENDELEY_CLIENT_ID, common.MENDELEY_CLIENT_SECRET)

        count = 0
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        with codecs.open(file, encoding="utf-16") as tsv:
            for line in csv.reader(tsv, delimiter="\t"):

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                if count == 1:
                    continue

                publisher_id = line[0]
                doi = line[1]
                issn = line[2]
                data = json.loads(line[3])

                tlogger.info(str(count-1) + ". Retrieving Mendelez saves for: " + doi)

                new_saves_value = None
                try:
                    new_saves_value = mendeley.get_saves(doi)
                except:
                    tlogger.info("General Exception - Mendelez API failed for %s. Moving to next article..." % doi)

                if new_saves_value:
                    data['mendeley_saves'] = new_saves_value

                    extra_values = {
                        'doi': doi,
                        'issn': issn,
                    }

                    try:
                        article = PublishedArticle.objects.get(publisher_id=publisher_id, article_doi=doi)
                        old_saves_value = article.mendeley_saves
                        extra_values.update({
                            'article_type': article.article_type,
                            'subject_category': article.subject_category,
                            'custom': article.custom,
                            'custom_2': article.custom_2,
                            'custom_3': article.custom_3,
                            'article_title': article.article_title,
                        })
                    except PublishedArticle.DoesNotExist:
                        old_saves_value = 0

                    run_alerts(
                        check_ids=['mendeley-saves-exceeds-integer', 'mendeley-saves-percentage-change'],
                        publisher_id=publisher_id,
                        product_id=product_id,
                        pipeline_id=pipeline_id,
                        job_id=job_id,
                        old_value=old_saves_value,
                        new_value=new_saves_value,
                        extra_values=extra_values,
                    )

                row = """%s\t%s\t%s\t%s\n""" % (publisher_id, doi, issn, json.dumps(data))

                target_file.write(row)

        target_file.close()

        send_alert_notifications(
            check_ids=['mendeley-saves-exceeds-integer', 'mendeley-saves-percentage-change'],
            publisher_id=publisher_id,
            product_id=product_id,
            pipeline_id=pipeline_id,
            job_id=job_id,
        )

        task_args['input_file'] = target_file_name
        task_args['count'] = count

        return task_args
