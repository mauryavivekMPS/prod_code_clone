from ivetl.validators.base import BaseValidator


class BundleDefinitionValidator(BaseValidator):

    def validate_files(self, files, issns=[], crossref_username=None, crossref_password=None, increment_count_func=None):
        errors = []
        total_count = 0
        return total_count, errors
