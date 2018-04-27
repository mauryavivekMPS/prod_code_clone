import re


class ValidationError(Exception):
    def __init__(self, error):
        message = "Validation Error: " + str(error)
        super(ValidationError, self).__init__(message)


class BaseValidator(object):

    MAX_ERRORS = 50

    def validate_files(self, files, issns=[], publisher_id=None, crossref_username=None, crossref_password=None, increment_count_func=None, second_level_validation=False):
        raise NotImplementedError

    def format_error(self, file_name, line_number, message):
        return "%s : %s - %s" % (file_name, line_number, message)

    def parse_errors(self, raw_errors):
        error_list = []
        error_regex = re.compile('^.+ : (\d+) - (.*)$')
        for error in raw_errors:
            m = error_regex.match(error)
            if m:
                line_number, message = m.groups()
                error_list.append({'line_number': line_number, 'message': message})
        return error_list
