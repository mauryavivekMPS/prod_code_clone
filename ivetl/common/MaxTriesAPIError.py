class MaxTriesAPIError(Exception):

    def __init__(self, error_count):

        message = "Maximum errors reached for API calls: " + str(error_count) + " errors"
        super(MaxTriesAPIError, self).__init__(message)

