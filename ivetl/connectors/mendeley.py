from mendeley import Mendeley
from mendeley.exception import MendeleyException
from ivetl.connectors.base import BaseConnector


class MendeleyConnector(BaseConnector):

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    def get_saves(self, doi):
        mendeley = Mendeley(self.client_id, self.client_secret)
        session = mendeley.start_client_credentials_flow().authenticate()

        saves = 0

        try:
            catalog = session.catalog.by_identifier(doi=doi, view='stats')

            acceptable_statuses = [
                "Lecturer",
                "Lecturer > Senior Lecturer",
                "Professor",
                "Professor > Associate Professor",
                "Researcher",
                "Student  > Doctoral Student",
                "Student  > Master",
                "Student  > Ph. D. Student",
                "Student  > Postgraduate",
            ]

            for status, saves_for_status in catalog.reader_count_by_academic_status.items():
                if status in acceptable_statuses:
                    saves += saves_for_status

        except MendeleyException:
            # the DOI is not found, swallow the exception
            pass

        return saves
