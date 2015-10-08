class ValidationError(Exception):
    def __init__(self, error):
        message = "Validation Error: " + str(error)
        super(ValidationError, self).__init__(message)


class BaseValidator(object):
    def validate_files(self, files, publisher_id):
        raise NotImplementedError
