import csv
import datetime
from ivetl.celery import app
from ivetl.pipelines.task import Task
from ivetl.pipelines.publishedarticles import UpdatePublishedArticlesPipeline
from ivetl.models import PublishedArticle, PublishedArticleValues, CitableSection, ValueMapping, ValueMappingDisplay
from ivetl.common import common
from ivetl.matchers import value as value_matcher


@app.task
class ResolvePublishedArticlesData(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        product = common.PRODUCT_BY_ID[product_id]

        file = task_args['input_file']
        total_count = task_args['count']

        now = datetime.datetime.now()

        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        electronic_issn_lookup = UpdatePublishedArticlesPipeline.generate_electronic_issn_lookup(publisher_id, product_id)

        # build some lists and dicts of article type mappings
        all_article_type_mappings = ValueMapping.objects.filter(publisher_id=publisher_id, mapping_type='article_type')
        canonical_article_type_by_original_value = {}
        all_canonical_values = set()
        for mapping in all_article_type_mappings:
            canonical_article_type_by_original_value[mapping.original_value] = mapping.canonical_value
            all_canonical_values.add(mapping.canonical_value)

        with open(file, encoding='utf-8') as tsv:
            count = 0
            for line in csv.reader(tsv, delimiter='\t'):

                count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

                # skip header row
                if count == 1:
                    continue

                doi = line[1]
                tlogger.info("Processing #%s : %s" % (count - 1, doi))

                # grab the canonical article record that we're operating on
                try:
                    article = PublishedArticle.objects.get(publisher_id=publisher_id, article_doi=doi)
                except PublishedArticle.DoesNotExist:
                    tlogger.info("DOI does not exist in published_article table")
                    continue

                # resolve policy: if a value from source=custom is present it always wins
                for field in ['article_type', 'subject_category', 'editor', 'custom', 'custom_2', 'custom_3']:
                    new_value = None
                    try:
                        v = PublishedArticleValues.objects.get(article_doi=doi, publisher_id=publisher_id, source='custom', name=field)
                        new_value = v.value_text
                    except PublishedArticleValues.DoesNotExist:
                        pass

                    if not new_value:
                        try:
                            v = PublishedArticleValues.objects.get(article_doi=doi, publisher_id=publisher_id, source='pa', name=field)
                            new_value = v.value_text
                        except PublishedArticleValues.DoesNotExist:
                            pass

                    # update the canonical if there is any non Null/None value (note that "None" is a value)
                    if new_value:

                        # special processing for value-mapped fields
                        if field == 'article_type':
                            # 1. get clean, simplified version of term
                            simplified_article_type = value_matcher.simplify_value(new_value)

                            # 2.1. look for exact match
                            new_canonical_value = canonical_article_type_by_original_value.get(simplified_article_type)

                            # 2.2. compare it to existing terms for close match
                            best_ratio_so_far = 0
                            best_match_so_far = None
                            if not new_canonical_value:
                                for existing_canonical_value in all_canonical_values:
                                    match, ratio = value_matcher.match_simplified_values(simplified_article_type, existing_canonical_value)

                                    if match:
                                        if ratio > best_ratio_so_far:
                                            best_match_so_far = existing_canonical_value

                            # 3. if match, then add to mapping table
                            if best_match_so_far:
                                new_canonical_value = best_match_so_far

                            # 4. if no match, then add display table (with original version) and add to mapping table
                            if not new_canonical_value:
                                new_canonical_value = simplified_article_type

                                ValueMapping.objects.create(
                                    publisher_id=publisher_id,
                                    mapping_type='article_type',
                                    original_value=new_value,
                                    canonical_value=new_canonical_value
                                )

                                new_display_value = new_value

                                ValueMappingDisplay.objects.create(
                                    publisher_id=publisher_id,
                                    mapping_type='article_type',
                                    canonical_value=new_canonical_value,
                                    display_value=new_display_value,
                                )

                                # add to in-memory lookup
                                canonical_article_type_by_original_value[new_value] = new_canonical_value

                            new_value = new_canonical_value

                        setattr(article, field, new_value)

                # update citable section flag
                if not product['cohort'] and article.article_type:
                    electronic_issn = electronic_issn_lookup.get(article.article_journal_issn)
                    if electronic_issn:
                        try:
                            CitableSection.objects.get(
                                publisher_id=publisher_id,
                                journal_issn=electronic_issn,
                                article_type=article.article_type
                            )
                            article.is_tr_citable = True
                        except CitableSection.DoesNotExist:
                            article.is_tr_citable = False

                article.updated = now
                article.save()

        if pipeline_id == 'custom_article_data':
            self.pipeline_ended(publisher_id, product_id, pipeline_id, job_id, tlogger, send_notification_email=True, notification_count=count, show_alerts=task_args['show_alerts'])

        task_args['count'] = count
        return task_args
