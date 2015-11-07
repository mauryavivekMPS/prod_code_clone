import csv
import codecs
import json
import datetime
from ivetl.celery import app
from ivetl.models import Published_Article, Article_Citations, Publisher_Vizor_Updates
from ivetl.pipelines.task import Task


@app.task
class InsertScopusIntoCassandra(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        file = task_args[self.INPUT_FILE]
        count = 0
        updated_date = datetime.datetime.today()

        with codecs.open(file, encoding="utf-16") as tsv:

            for line in csv.reader(tsv, delimiter="\t"):

                count += 1
                if count == 1:
                    continue

                publisher_id = line[0]
                doi = line[1]
                citations = json.loads(line[2])

                for data in citations:

                    Article_Citations.create(
                        publisher_id=publisher_id,
                        article_doi=doi,
                        citation_doi=data['doi'],
                        citation_scopus_id=data['scopus_id'],
                        citation_date=datetime.datetime.strptime(data['date'], '%Y-%m-%d'),
                        citation_first_author=data['first_author'],
                        citation_issue=data['issue'],
                        citation_journal_issn=data['journal_issn'],
                        citation_journal_title=data['journal_title'],
                        citation_pages=data['pages'],
                        citation_source_scopus = True,
                        citation_title=data['title'],
                        citation_volume=data['volume'],
                        citation_count=1,
                        updated=updated_date,
                        created=updated_date,
                        is_cohort=data['is_cohort']
                    )

                Published_Article.objects(publisher_id=publisher_id, article_doi=doi).update(citations_updated_on=updated_date)

                tlogger.info("---")
                tlogger.info(str(count-1) + ". " + publisher_id + " / " + doi + ": Inserted " + str(len(citations)) + " citations.")

            tsv.close()

            Publisher_Vizor_Updates.create(
                publisher_id=publisher_id,
                vizor_id=pipeline_id,
                updated=updated_date,
            )

        task_args[self.COUNT] = count
        return task_args
