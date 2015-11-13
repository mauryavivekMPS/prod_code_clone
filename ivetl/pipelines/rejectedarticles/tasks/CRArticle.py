class CRArticle:

    def __init__(self):
        self.cites = 0
        self.rejectiondate = ""
        self.rejectreason = ""
        self.bpmanuscripid = ""
        self.doi = ""
        self.bptitle = ""
        self.journal = ""
        self.status = ""
        self.author_first_name = ""
        self.author_last_name = ""
        self.publishdate = ""
        self.xreftitle = ""
        self.xrefauthor_surnames = []
        self.xrefcoauthors = []
        self.authormatchscore = 0.0
        self.xreftitlescore = 0.0
        self.bpeditor = ""
        self.publisher = ""

    def setxrefdetails(self, item, issn_journals):

        j = item

        self.doi = j['DOI']

        if len(j['title']) > 0:
            self.bptitle = j['title'][0].replace("\n", "").replace("\r", "")
        else:
            self.bptitle = ""

        year = j['issued']['date-parts'][0][0]

        month = 1
        if len(j['issued']['date-parts'][0]) >= 2:
            month = j['issued']['date-parts'][0][1]

        day = 1
        if len(j['issued']['date-parts'][0]) >= 3:
            day = j['issued']['date-parts'][0][2]

        self.publishdate = str(month) + '/' + str(day) + '/' + str(year)

        issn = ""

        if 'ISSN' in j:
            issn = j['ISSN'][0]

        if issn in issn_journals:
            self.journal = issn_journals[issn][0]
            self.publisher = issn_journals[issn][1]
        else:
            if 'container-title' in j and len(j['container-title']) > 0:
                self.journal = j['container-title'][0]

            if 'publisher' in j:
                self.publisher = j['publisher']

        if 'author' in j:

            authors = j['author']
            first_author = True

            for a in authors:

                if 'given' not in a:
                    a['given'] = ''

                if 'family' not in a:
                    a['family'] = ''

                if first_author:
                    self.author_last_name = a['family']
                    if 'given' in a:
                        self.author_first_name = a['given']
                    first_author = False
                    continue

                self.xrefcoauthors.append(a['family'] + "," + a['given'])





