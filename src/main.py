#!/usr/bin/python3

import unittest

import sys
import utils
from parser import Char_stream # our library that will help us with lexical analysis/tokenization

def skip_space(char_stream: Char_stream):
    while not char_stream.is_over() and (char_stream.peek() == ' ' or char_stream.peek() == '\n'):
        char_stream.advance()

def scan_id(char_stream: Char_stream, advance: bool):
    if advance:
        char_stream.advance()
    value = ''
    if not char_stream.peek().isalpha():
        raise SyntaxError("Expected an identifier to start with an alpha")
    while char_stream.peek().isalpha() or char_stream.peek().isdigit():
        value += char_stream.advance()
    return value

def expr(char_stream: Char_stream, advance: bool, scope: dict, flags: utils.Map):
    left = term(char_stream, advance, scope, flags)

    while True:
        if char_stream.peek() == '+':
            left += term(char_stream, True, scope, flags)
        elif char_stream.peek() == '-':
            left -= term(char_stream, True, scope, flags)
        else:
            return left

def term(char_stream: Char_stream, advance: bool, scope: dict, flags: utils.Map):
    left = prim(char_stream, advance, scope, flags)

    while True:
        if char_stream.peek() == '*':
            left *= prim(char_stream, True, scope, flags)
        elif char_stream.peek() == '/':
            left /= prim(char_stream, True, scope, flags)
        else:
            return left

def prim(char_stream: Char_stream, advance: bool, scope: dict, flags: utils.Map):
    if advance:
        char_stream.advance()
    skip_space(char_stream)
    if char_stream.peek() == '(':
        value = expr(char_stream, True, scope, flags)
        value_ptr = [value]
        if char_stream.peek() != ')':
            raise SyntaxError("Missing ')'")
        char_stream.advance() # eat ')'
        skip_space(char_stream)
        chain_obj(char_stream, value_ptr, scope) # wrap up method chaining to enable '(a).a' syntax
        value = value_ptr[0]
        return value

    return interpret_obj_and_chain(char_stream, False, scope, flags) # use the complete variant of parse_obj supporting method chaining

def chain_obj(char_stream: Char_stream, value_ptr: list, scope: dict):
    while True:
        if callable(value_ptr[0]) and char_stream.peek() == '(':
            args = [] # a variable to store the evaluated arguments

            cs = Char_stream(char_stream.source, char_stream.c)
            char_stream.advance()
            skip_space(char_stream)
            if char_stream.peek() == ')':
                char_stream.advance() # eat ')'
                skip_space(char_stream)
                value_ptr[0] = value_ptr[0]() # evaluate the function with no arguments passed
                continue
            else:
                char_stream.set_cs(cs) # reset the char stream to last matched '('

            while True:
                args.append(expr(char_stream, True, scope, utils.Map({'temFlag': True, 'isKey': False,})))
                if char_stream.peek() == ',':
                    continue
                elif char_stream.peek() == ')':
                    char_stream.advance()
                    skip_space(char_stream)
                    value_ptr[0] = value_ptr[0](*args) # evaluate the function with x number of arguments passed
                    break
                else:
                    raise SyntaxError("Unexpected char while parsing a function: " + char_stream.current)
        elif type(value_ptr[0]) == dict and char_stream.peek() == '.':
            identifier = scan_id(char_stream, True)
            skip_space(char_stream)
            value_ptr[0] = value_ptr[0][identifier]
            continue

        else:
            break


def interpret_obj_and_chain(char_stream: Char_stream, advance: bool, scope: dict, flags: utils.Map):
    value = interpret_obj(char_stream, advance, scope, flags)
    value_ptr = [ value ]
    chain_obj(char_stream, value_ptr, scope)
    return value_ptr[0]

def interpret_obj(char_stream: Char_stream, advance: bool, scope: dict, flags: utils.Map):
    if advance:
        char_stream.advance()

    skip_space(char_stream)

    if char_stream.peek().isdigit():
        value = ''
        while char_stream.peek().isdigit():
            value += char_stream.advance()
        skip_space(char_stream)
        return int(value, 10) # base 10

    elif char_stream.peek().isalpha() and flags.temFlag: # identifier type check using prefix checking
        identifier = scan_id(char_stream, False)
        skip_space(char_stream)

        # print('flags: ', tem, flags)

        if flags.isKey:
            return identifier

        if identifier not in scope.keys():
            raise NameError(identifier + " not defined")
        return scope[identifier]

    elif char_stream.peek() == '{':
        obj = {}
        obj_scope = {}
        cs = Char_stream(char_stream.source, char_stream.c)
        char_stream.advance()
        skip_space(char_stream)
        if char_stream.peek() == '}':
            char_stream.advance() # eat '}'
            skip_space(char_stream)
            return obj
        else:
            char_stream.set_cs(cs) # reset the char stream back to last '{' and proceed with the parsing

        utils.deep_update(obj_scope, scope)
        
        while True:
            key = interpret_obj(char_stream, True, scope, utils.Map({'temFlag': True, 'isKey': True,}))
            # print('key: ', key)
            if char_stream.peek() == ':':
                value = expr(char_stream, True, obj_scope, utils.Map({'temFlag': True, 'isKey': False,}))
                utils.deep_update(obj_scope, {key: value})
                utils.deep_update(obj, {key: value})

                if char_stream.peek() == '}':
                    char_stream.advance() # eat '}'
                    skip_space(char_stream)
                    return obj
                elif char_stream.peek() == ',':
                    continue
                else:
                    # print(char_stream.current)
                    raise SyntaxError("Unexpected char " + char_stream.current)
            else:
                raise SyntaxError("Unexpected char " + char_stream.current)
    else:
        raise SyntaxError("Unexpected char " + char_stream.current)


# because of our recursion logic, the function will fail to check -
# if there are extra characters that give an error: for example: "{}}", "())" and similar.
def interpret_object(stream: Char_stream, scope): 
    default_flags = utils.Map({})
    obj = interpret_obj(stream, False, scope, default_flags)
    if not stream.is_over():
        raise SyntaxError('unmatched ' + stream.current)
    return obj


def main():
    text = Char_stream(r'''{a: 12, b: 11, c: {b: 1, d: {a: 21}}, d1: ((c.d.a)*2+1), d2: 110, f1: func(1,2), f2: func1() }''')
    text = Char_stream(r'''{ c: {b: 1, d: {a: 21}}, d1: (((c.d).a)*2+1), f: (func)(1+1, 2*2) }''')
    # text = Char_stream('{a:1}')
    # text = Char_stream('{}')
    scope = {'func': lambda x,y: x+y, 'func1': lambda: print('hi!'),}

    obj = interpret_object(text, scope)

    utils.export_json(obj)
    # print(obj)

class TestLanguage(unittest.TestCase):
    def __init__(self, *args):
        super().__init__(*args)
        self.ctx = {}

    def test_foo_object(self):
        foo = interpret_object(Char_stream('{foo: 1}'), self.ctx)
        self.assertEqual(str(foo), "{'foo': 1}")

    def test_empty_object(self):
        empty = interpret_object(Char_stream('{}'), self.ctx)
        self.assertEqual(str(empty), '{}')

    def test_nested_object(self):
        nested = interpret_object(Char_stream('{foo:{zoo: {}}}'), self.ctx)
        self.assertEqual(str(nested), "{'foo': {'zoo': {}}}")

    def test_nested_merge(self):
        text = r'''
            {
              foo: { zoo: { a:1 } },
              foo: { zoo: { b:2 } }
            }
        '''
        expected = "{'foo': {'zoo': {'a': 1, 'b': 2}}}"
        nested_merge = interpret_object(Char_stream(text), self.ctx)
        self.assertEqual(str(nested_merge), expected)

    def test_object_expression(self):
        text = '{ foo: (1+1)*10 }'
        expression = interpret_object(Char_stream(text), self.ctx)
        self.assertEqual(str(expression), "{'foo': 20}")

    def test_object_chainable(self):
        text = r'''
          {
            foo: { b: 1 },
            boo: foo.b
          }
        '''
        expected = "{'foo': {'b': 1}, 'boo': 1}"
        chainable = interpret_object(Char_stream(text), self.ctx)
        self.assertEqual(str(chainable), expected)

def unit_test():
    unittest.main()


# Snippet 14 - displaying our json data
def json_export():
    scope =  {'func': lambda x,y: x+y,} # our parser can evaluate functions
    default_flags = utils.Map({})
    utils.export_json(interpret_obj(Char_stream('{' + input() + '}'), False, scope, default_flags))
    # note that 'utils.export_json' is an alternative to 'json.dump' supported by Python Standard Library
    # more details on that here: https://docs.python.org/3/library/json.html

# to run unit tests:
# > python3 -m unittest -v main.py
if __name__ == '__main__':
    if(len(sys.argv) >= 1):
        main()
    else:
        unit_test()

    # json_export()
