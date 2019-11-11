import csv
import datetime

from ivetl import value_mappings
from ivetl.celery import app
from ivetl.common import common
from ivetl.matchers import value as value_matcher
from ivetl.models import PublishedArticle, PublishedArticleValues, CitableSection, ValueMapping, ValueMappingDisplay
from ivetl.pipelines.customarticledata import CustomArticleDataPipeline
from ivetl.pipelines.publishedarticles import UpdatePublishedArticlesPipeline
from ivetl.pipelines.task import Task


@app.task
class ResolvePublishedArticlesData(Task):

    def run_task(self, publisher_id, product_id, pipeline_id, job_id, work_folder, tlogger, task_args):
        product = common.PRODUCT_BY_ID[product_id]

        file = task_args.get('input_file')

        now = datetime.datetime.now()

        electronic_issn_lookup = UpdatePublishedArticlesPipeline.generate_electronic_issn_lookup(publisher_id, product_id)

        # build some lists and dicts of all the value mappings
        all_value_mappings = {}
        canonical_value_by_original_value = {}
        display_value_by_canonical_value = {}
        all_canonical_values = {}
        for field in value_mappings.MAPPING_TYPES:
            all_value_mappings[field] = ValueMapping.objects.filter(publisher_id=publisher_id, mapping_type=field)
            canonical_value_by_original_value[field] = {}
            all_canonical_values[field] = set()
            for mapping in all_value_mappings[field]:
                canonical_value_by_original_value[field][mapping.original_value] = mapping.canonical_value
                all_canonical_values[field].add(mapping.canonical_value)
            display_value_by_canonical_value[field] = {}
            for d in ValueMappingDisplay.objects.filter(publisher_id=publisher_id, mapping_type=field):
                display_value_by_canonical_value[field][d.canonical_value] = d.display_value

        all_articles = []
        if file:
            with open(file, encoding='utf-8') as tsv:
                line_count = 0
                for line in csv.reader(tsv, delimiter='\t'):
                    line_count += 1

                    # skip header row
                    if line_count == 1:
                        continue

                    doi = common.normalizedDoi(line[1])
                    try:
                        all_articles.append(PublishedArticle.objects.get(publisher_id=publisher_id, article_doi=doi))
                    except PublishedArticle.DoesNotExist:
                        tlogger.info("DOI %s does not exist in published_article table, skipping" % doi)
                        continue
        else:
            all_articles = PublishedArticle.objects.filter(publisher_id=publisher_id).limit(1000000).fetch_size(1000)

        total_count = len(all_articles) * 2  # twice around the main loop
        self.set_total_record_count(publisher_id, product_id, pipeline_id, job_id, total_count)

        all_new_values = {}

        count = 0

        # first loop, get all the values and execute the value mapping
        tlogger.info('First loop, getting values and running value mapping')
        for article in all_articles:
            count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

            tlogger.info("Processing #%s : %s" % (count - 1, article.article_doi))

            # resolve policy: if a value from source=custom is present it always wins
            for field in CustomArticleDataPipeline.FOAM_FIELDS:
                new_value = None
                try:
                    v = PublishedArticleValues.objects.get(article_doi=article.article_doi, publisher_id=publisher_id, source='custom', name=field)
                    new_value = v.value_text
                except PublishedArticleValues.DoesNotExist:
                    pass

                if not new_value:
                    try:
                        v = PublishedArticleValues.objects.get(article_doi=article.article_doi, publisher_id=publisher_id, source='pa', name=field)
                        new_value = v.value_text
                    except PublishedArticleValues.DoesNotExist:
                        pass

                # hard default to "None"
                if not new_value:
                    new_value = "None"

                all_new_values[(article.article_doi, field)] = new_value

                # special processing for value-mapped fields
                if field in value_mappings.MAPPING_TYPES:

                    # look for exact match
                    new_canonical_value = canonical_value_by_original_value[field].get(new_value)

                    alt_simple_plural_simplified_value = None

                    if not new_canonical_value:
                        # get clean, simplified version of term
                        simplified_value = value_matcher.simplify_value(new_value)

                        # Note: this little dance below is intended to handle plurals of non-dictionary words

                        # if it ends with a single 's' look for a match without it, if not, add one and look for that
                        if simplified_value.endswith('s'):
                            if not simplified_value.endswith('ss'):
                                alt_simple_plural_simplified_value = simplified_value[:-1]
                        else:
                            alt_simple_plural_simplified_value = simplified_value + 's'

                    # compare it to existing terms for close match
                    best_ratio_so_far = 0
                    best_match_so_far = None
                    if not new_canonical_value:
                        for existing_canonical_value in all_canonical_values[field]:

                            # test the regular simplified value
                            match, ratio = value_matcher.match_simplified_values(simplified_value, existing_canonical_value)
                            if match:
                                if ratio > best_ratio_so_far:
                                    best_match_so_far = existing_canonical_value

                            # now test the alt value
                            if alt_simple_plural_simplified_value:
                                match, ratio = value_matcher.match_simplified_values(alt_simple_plural_simplified_value, existing_canonical_value)
                                if match:
                                    if ratio > best_ratio_so_far:
                                        best_match_so_far = existing_canonical_value

                    # if match, then add to mapping table
                    if best_match_so_far:
                        new_canonical_value = best_match_so_far

                        ValueMapping.objects.create(
                            publisher_id=publisher_id,
                            mapping_type=field,
                            original_value=new_value,
                            canonical_value=new_canonical_value
                        )

                        canonical_value_by_original_value[field][new_value] = new_canonical_value

                        tlogger.info('Adding a new ValueMapping to existing ValueMappingDisplay: %s -> %s' % (new_value, new_canonical_value))

                    # if no match, then add display table (with original version) and add to mapping table
                    if not new_canonical_value:
                        new_canonical_value = simplified_value

                        ValueMapping.objects.create(
                            publisher_id=publisher_id,
                            mapping_type=field,
                            original_value=new_value,
                            canonical_value=new_canonical_value
                        )

                        new_display_value = new_value

                        ValueMappingDisplay.objects.create(
                            publisher_id=publisher_id,
                            mapping_type=field,
                            canonical_value=new_canonical_value,
                            display_value=new_display_value,
                        )

                        tlogger.info('Adding a new ValueMapping and ValueMappingDisplay: %s -> %s -> %s' % (new_value, new_canonical_value, new_display_value))

                        # add to in-memory lookups
                        canonical_value_by_original_value[field][new_value] = new_canonical_value
                        display_value_by_canonical_value[field][new_canonical_value] = new_display_value

        # second loop, save changes to db
        tlogger.info('Second loop, using updated value mapping and writing to db')
        for article in all_articles:
            count = self.increment_record_count(publisher_id, product_id, pipeline_id, job_id, total_count, count)

            tlogger.info("Processing #%s : %s" % (count - 1, article.article_doi))

            # resolve policy: if a value from source=custom is present it always wins
            for field in CustomArticleDataPipeline.FOAM_FIELDS:

                # grab the value from the local cache built in the previous loop
                new_value = all_new_values.get((article.article_doi, field))

                if field in value_mappings.MAPPING_TYPES:
                    # pull out the values found/mapped in the previous loop
                    new_canonical_value = canonical_value_by_original_value[field][new_value]
                    new_value = display_value_by_canonical_value[field][new_canonical_value]

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

        task_args['count'] = count
        return task_args
