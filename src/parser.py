class EndLine(Exception):
    pass

class Char_stream:

    def __init__(self, source, c = 0):
        self.c = c # counter for our token stream
        self.source = source

    @property
    def current(self):
        if not self.c < len(self.source):
            raise EndLine("EndLine Error!")
        return self.source[self.c]

    def next_char(self):
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

    def set_cs(self, char_stream):
        self.source = char_stream.source
        self.c = char_stream.c

class Token():
    pass

# reuse Char_stream to extend Lexer and then Parser - adding new methods in the future, and vice versa
class Lexer():

    def __init__(self, expression):
        self.char_stream = Char_stream(expression)
        self.tokens = [] # List<Token>

    def lex(): # tokenize
        return self.tokens

# use Parser with Lexer to generate AST
class Parser(): 

    def __init__(self, expression):
        self.tokens = Lexer(expression).lex()
        self.ast = {}
