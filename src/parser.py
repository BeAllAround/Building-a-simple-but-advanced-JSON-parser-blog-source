class EndLine(Exception):
    pass

class CharStream:
    pass

class CharStream:

    def __init__(self, source: str, c: int = 0):
        self.c = c # counter for our stream
        self.source = source

    @property
    def current(self):
        if not self.c < len(self.source):
            raise EndLine("EndLine Error!")
        return self.source[self.c]

    def advance(self):
        if self.c >= len(self.source):
            raise EndLine("EndLine Error!")
        char = self.source[self.c]
        self.c += 1
        return char

    def peek(self):
        # if self.is_over():
            # return False # return False when there is nothing to match
        return self.current

    def is_over(self):
        return not self.c < len(self.source)

    def set_cs(self, char_stream: CharStream):
        self.source = char_stream.source
        self.c = char_stream.c

class Token:

    def __init__(self, tp, char): # TODO
        self.tp = tp
        self.char = char

# reuse CharStream to extend Lexer and then Parser - adding new methods as we go
class Lexer:

    def __init__(self, expression: str):
        self.char_stream: CharStream = CharStream(expression)
        self.tokens: list = [] # List<Token>

    def lex(self): # tokenize
        return self.tokens

# use Parser with Lexer to generate AST
class Parser: 

    def __init__(self, expression: str):
        self.tokens = Lexer(expression).lex()
        self.ast = {}
