from collections import defaultdict
from ivetl.models import ArticleSkipRule


def suppl_in_doi(values):
    return '_suppl' in values['article_doi']


ARTICLE_SKIPPER_TYPES = {
    'suppl_in_doi': {
        'name': '"_supple" in article DOI',
        'function': suppl_in_doi,
    },
}


class ArticleSkipper(object):
    def __init__(self, publisher_id):
        self.skip_rules_by_issn = defaultdict(list)
        for r in ArticleSkipRule.objects.filter(publisher_id=publisher_id):
            self.skip_rules_by_issn[r.issn].append(r)

    def should_skip_article_for_journal(self, issn, values):
        if issn in self.skip_rules_by_issn:
            for r in self.skip_rules_by_issn[issn]:
                if r.rule in ARTICLE_SKIPPER_TYPES:
                    if ARTICLE_SKIPPER_TYPES[r.rule]['function'](values):
                        return True
        return False
