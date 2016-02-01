class AuthorizationAPIError(Exception):
    def __init__(self, error=None):
        message = "Authorization Error"
        if error:
            message += ": %s" % error
        super(AuthorizationAPIError, self).__init__(message)


class MaxTriesAPIError(Exception):
    def __init__(self, error_count):
        message = "Maximum errors reached for API calls: " + str(error_count) + " errors"
        super(MaxTriesAPIError, self).__init__(message)


class BaseConnector(object):
    pass
