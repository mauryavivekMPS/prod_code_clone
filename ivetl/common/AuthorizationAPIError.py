class AuthorizationAPIError(Exception):

    def __init__(self, error):

        message = "Authorization Error: " + str(error)
        super(AuthorizationAPIError, self).__init__(message)