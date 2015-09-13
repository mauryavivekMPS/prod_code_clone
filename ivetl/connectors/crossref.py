import requests
from bs4 import BeautifulSoup
from ivetl.connectors.base import BaseConnector


class CrossrefConnector(BaseConnector):
    BASE_CITATION_URL = 'https://doi.crossref.org/servlet/getForwardLinks'
    BASE_ARTICLE_URL = 'http://api.crossref.org/works/'

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def get_citations(self, doi):
        url = '%s?usr=%s&pwd=%s&doi=%s&format=unixsd' % (self.BASE_CITATION_URL, self.username, self.password, doi)
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'xml')
        return [e.text for e in soup.find_all('doi')]

    def get_article(self, doi):
        url = '%s%s' % (self.BASE_CITATION_URL, doi)
        r = requests.get(url)

        try:
            article_json = r.json()
        except ValueError:
            article_json = None

        article = None

        if article_json:
            article_json = article_json['message']

            # date
            date_parts = article_json['issued']['date-parts'][0]
            citation_date = '%s-%s-%s' % date_parts

            # author
            author_parts = article_json['author'][0]
            author = '%s,%s' % (author_parts['family'], author_parts['given'])

            # issue
            issue = article_json['issue']

            # journal ISSN
            journal_issn = article_json['ISSN'][0]

            # journal title
            journal_title = article_json['title'][0]

            # pages
            pages = article_json['page']

            # title
            title = article_json['container-title']

            # volume
            volume = article_json['volume']

            article = {
                'doi': doi,
                'date': citation_date,
                'first_author': author,
                'issue': issue,
                'journal_issn': journal_issn,
                'journal_title': journal_title,
                'pages': pages,
                'title': title,
                'volume': volume,
                'source': 'Crossref',
            }

        return article
