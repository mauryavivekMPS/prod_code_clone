import requests
from cassandra.cqlengine.query import BatchQuery
from ivetl.models.issn_journal import IssnJournal
from ivetl.celery import app
from ivetl.pipelines.task import Task


@app.task
class XREFJournalCatalogTask(Task):
    ITEMS_PER_PAGE = 50

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):

        total_count = 0  # we don't know this up front
        count = 0
        offset = 0

        while offset != -1:

            attempt = 0
            max_attempts = 3
            r = None
            success = False

            while not success and attempt < max_attempts:
                try:
                    url = 'http://api.crossref.org/journals?rows=' + str(self.ITEMS_PER_PAGE) + '&offset=' + str(offset)
                    tlogger.info("Searching CrossRef for: " + url)
                    r = requests.get(url)

                    success = True

                except Exception:
                    attempt += 1
                    tlogger.warning("Error connecting to Crossref API.  Trying again.")
                    if attempt > max_attempts:
                        raise

            xrefdata = r.json()

            if 'ok' in xrefdata['status'] and len(xrefdata['message']['items']) > 0:

                b = BatchQuery()

                # take a best guess at a total
                total_count += len(xrefdata['message']['items'])
                self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

                for i in xrefdata['message']['items']:

                    issn1 = ""
                    if len(i['ISSN']) > 0:
                        issn1 = i['ISSN'][0].strip()

                    issn2 = ""
                    if len(i['ISSN']) > 1:
                        issn2 = i['ISSN'][1].strip()

                    journal = i['title']
                    publisher = i['publisher']

                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                    if issn1 != "":
                        IssnJournal.batch(b).create(issn=issn1, journal=journal, publisher=publisher)
                        #print(issn1)

                    if issn2 != "":
                        IssnJournal.batch(b).create(issn=issn2, journal=journal, publisher=publisher)
                        #print(issn2)

                    #print(issn1 + "," + issn2 + ":: " + journal + " / " + publisher)

                b.execute()
                offset += self.ITEMS_PER_PAGE

            else:
                offset = -1

        task_args['count'] = count
        return task_args
