from collections import defaultdict
from ivetl.models import ArticleSkipRule


def suppl_in_doi(doi, values):
    return '_suppl' in doi


ARTICLE_SKIPPER_TYPES = {
    'suppl_in_doi': {
        'name': '"_supple" in article DOI',
        'function': suppl_in_doi,
    },
}

ARTICLE_SKIPPER_TYPE_CHOICES = [(skipper_id, skipper['name']) for skipper_id, skipper in ARTICLE_SKIPPER_TYPES.items()]


class ArticleSkipper(object):

    # Note: the skipper here supports multiple rules per ISSN, but the rest of the app assumes just one

    def __init__(self, publisher_id, is_cohort):
        self._publisher_id = publisher_id
        self._is_cohort = is_cohort
        self.skip_rules_by_issn = defaultdict(list)
        for r in ArticleSkipRule.objects.filter(publisher_id=publisher_id, is_cohort=is_cohort):
            self.skip_rules_by_issn[r.issn].append(r)

    @property
    def publisher_id(self):
        return self._publisher_id

    @property
    def is_cohort(self):
        return self._is_cohort

    def should_skip_article_for_journal(self, doi, issn, values):
        if issn in self.skip_rules_by_issn:
            for r in self.skip_rules_by_issn[issn]:
                if r.rule in ARTICLE_SKIPPER_TYPES:
                    if ARTICLE_SKIPPER_TYPES[r.rule]['function'](doi, values):
                        return True
        return False
