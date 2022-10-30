class EndLine(Exception):
    pass

class Parser:

    def __init__(self, source, c = 0):
        self.c = c
        self.source = source

    @property
    def current(self):
        if not self.c < len(self.source):
            raise EndLine("EndLine Error!")
        return self.source[self.c]

    def next_token(self):
        if self.c > len(self.source):
            raise EndLine("EndLine Error!")
        self.c += 1

    def __eq__(self, toMatch):
        if self.is_over():
            return False # return False when there is nothing to match
        if type(toMatch) != str:
            raise Exception("Can't match non-str")
        return self.current == toMatch

    def is_over(self):
        return not self.c < len(self.source)

    def set_token(self, token):
        self.source = token.source
        self.c = token.c
