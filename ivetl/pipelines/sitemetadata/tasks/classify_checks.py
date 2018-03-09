import os
import re
import json
import codecs
import csv
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.models import HighwireMetadata, DrupalMetadata


@app.task
class ClassifyChecksTask(Task):
    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        file = task_args['input_file']
        total_count = task_args['count']

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        count = 0

        h20_metadata_by_site_url = {}
        h20_metadata_by_site_code = {}
        for journal in HighwireMetadata.objects.all():
            h20_metadata_by_site_url[journal.site_url[7:]] = journal
            h20_metadata_by_site_code[journal.site_code] = journal

        drupal_metadata_by_site_url = {}
        for journal in DrupalMetadata.objects.all():
            drupal_metadata_by_site_url[journal.site_url] = journal

        target_file_name = os.path.join(work_folder, "%s_uptimechecks_target.tab" % publisher_id)

        with codecs.open(target_file_name, 'w', 'utf-16') as target_file:
            target_file.write('CHECK_ID\tDATA\n')

            with codecs.open(file, encoding="utf-16") as tsv:
                for line in csv.reader(tsv, delimiter="\t"):

                    count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)
                    if count == 1:
                        continue

                    check = json.loads(line[1])

                    tlogger.info('Classifying check %s' % check['id'])

                    #
                    # join the checks with the metadata
                    #

                    hostname = check['hostname']
                    hostname_with_www = 'www.' + hostname

                    count += 1

                    h20_metadata = None
                    drupal_metadata = None
                    original_site_code = ''

                    if hostname in h20_metadata_by_site_url:
                        hostname_metadata = h20_metadata_by_site_url[hostname]
                        original_site_code = hostname_metadata.site_code

                        if original_site_code.startswith('bp_'):
                            site_code_without_prefix = original_site_code[3:]

                            if site_code_without_prefix in h20_metadata_by_site_code:
                                h20_metadata = h20_metadata_by_site_code[site_code_without_prefix]

                        else:
                            h20_metadata = h20_metadata_by_site_url[hostname]

                    elif hostname_with_www in h20_metadata_by_site_url:
                        h20_metadata = h20_metadata_by_site_url[hostname_with_www]

                    if hostname in drupal_metadata_by_site_url:
                        drupal_metadata = drupal_metadata_by_site_url[hostname]

                    #
                    # classify type of check
                    #

                    def _unknown_if_empty(value):
                        if not value or value == 'N/A' or value == 'Unknown':
                            return 'unknown'
                        else:
                            return value

                    check['site_name'] = 'unknown'
                    check['site_code'] = 'unknown'
                    check['publisher_name'] = 'unknown'
                    check['publisher_code'] = 'unknown'
                    check['drupal_launch_date'] = None

                    if h20_metadata:
                        check['site_name'] = _unknown_if_empty(h20_metadata.name)
                        check['site_code'] = _unknown_if_empty(h20_metadata.site_code)
                        check['publisher_code'] = _unknown_if_empty(h20_metadata.umbrella_code)
                        check['publisher_name'] = _unknown_if_empty(h20_metadata.publisher)

                    if drupal_metadata:
                        if check['site_name'] == 'unknown':
                            check['site_name'] = _unknown_if_empty(drupal_metadata.name)
                        check['site_code'] = _unknown_if_empty(drupal_metadata.site_code)
                        check['publisher_code'] = _unknown_if_empty(drupal_metadata.umbrella_code)
                        check['publisher_name'] = _unknown_if_empty(drupal_metadata.publisher)
                        if drupal_metadata.launch_date:
                            check['drupal_launch_date'] = self.to_json_date(drupal_metadata.launch_date)

                    name = check['name']
                    url = check['type']['http']['url']
                    if name.endswith('TOC') or url == '/content/current':
                        check_type = 'toc'
                    elif name.endswith('Article') or ('content' in url and url != '/content/current'):
                        check_type = 'article'
                    elif name.endswith('Search') or 'search' in url:
                        check_type = 'search'
                    elif check['account'] == 'primary' and 'content' not in url and 'search' not in url and not re.search('\d', url):
                        check_type = 'home'
                    elif check['account'] == 'tertiary':
                        check_type = 'home'
                    else:
                        check_type = 'other'

                    check['check_type'] = check_type

                    #
                    # classify type of site
                    #

                    site_type = 'unknown'
                    if drupal_metadata:
                        site_type = drupal_metadata.product
                    else:
                        if h20_metadata:
                            if h20_metadata.is_book == 'Y':
                                site_type = 'book'
                            elif original_site_code.startswith('bp_'):
                                site_type = 'benchpress'
                            elif h20_metadata.site_code == h20_metadata.counter_code:
                                site_type = 'umbrella'
                            else:
                                site_type = 'journal'
                        else:
                            if hostname.startswith('submit'):
                                site_type = 'benchpress'

                    check['site_type'] = site_type

                    #
                    # classify platform
                    #

                    site_platform = 'unknown'

                    if drupal_metadata:
                        site_platform = 'drupal'

                    elif h20_metadata:
                        dw_site_type = h20_metadata.dw_site_type
                        if dw_site_type:
                            site_platform = dw_site_type

                    check['site_platform'] = site_platform

                    # write out to target file
                    row = "%s\t%s\n" % (check['id'], json.dumps(check))
                    target_file.write(row)

        task_args['count'] = count
        task_args['input_file'] = target_file_name
        return task_args
