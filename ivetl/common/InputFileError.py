
class InputFileError(Exception):

    def __init__(self, file):
        self.file = file

