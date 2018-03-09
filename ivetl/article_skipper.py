from ivetl.models import ArticleSkipRule


def supple_in_doi(values):
    return '_supple' in values['article_doi']


ARTICLE_SKIPPER_TYPES = {
    'suppl_in_doi': {
        'name': '"_supple" in article DOI',
        'function': supple_in_doi,
    },
}


class ArticleSkipper(object):
    def __init__(self, publisher_id):
        pass


def should_skip_article(publisher_id, issn, values):
    pass
