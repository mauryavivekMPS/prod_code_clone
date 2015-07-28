
class InputFileError(Exception):

    file = ''
    line_num = ''
    line = ''

    def __init__(self, file):
        self.file = file

