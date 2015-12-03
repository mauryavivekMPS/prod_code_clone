import re


class ValidationError(Exception):
    def __init__(self, error):
        message = "Validation Error: " + str(error)
        super(ValidationError, self).__init__(message)


class BaseValidator(object):
    def validate_files(self, files, publisher_id):
        raise NotImplementedError

    def parse_errors(self, raw_errors):
        error_list = []
        error_regex = re.compile('^.+ : (\d+) - (.*)$')
        for error in raw_errors:
            m = error_regex.match(error)
            if m:
                line_number, message = m.groups()
                error_list.append({'line_number': line_number, 'message': message})
        return error_list
