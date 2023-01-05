#!/usr/bin/python3
import sys
import utils
from parser import Char_stream # our library that will help us with lexical analysis/tokenization

def skip_space(char_stream: Char_stream):
    while not char_stream.is_over() and (char_stream.peek() == ' ' or char_stream.peek() == '\n'):
        char_stream.advance()

def parse_id(char_stream: Char_stream, advance: bool):
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
        chain_main(char_stream, value_ptr, scope) # wrap up method chaining to enable '(a).a' syntax
        value = value_ptr[0]
        return value

    return parse_obj_and_chain(char_stream, False, scope, flags) # use the complete variant of parse_obj supporting method chaining

def chain_main(char_stream: Char_stream, value_ptr: list, scope: dict):
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
            identifier = parse_id(char_stream, True)
            skip_space(char_stream)
            value_ptr[0] = value_ptr[0][identifier]
            continue

        else:
            break


def parse_obj_and_chain(char_stream: Char_stream, advance: bool, scope: dict, flags: utils.Map):
    value = parse_obj(char_stream, advance, scope, flags)
    value_ptr = [value]
    chain_main(char_stream, value_ptr, scope)
    return value_ptr[0]

def parse_obj(char_stream: Char_stream, advance: bool, scope: dict, flags: utils.Map):
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
        identifier = parse_id(char_stream, False)
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
            key = parse_obj(char_stream, True, scope, utils.Map({'temFlag': True, 'isKey': True,}))
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
def parse_object(stream: Char_stream, scope): 
    default_flags = utils.Map({})
    obj = parse_obj(stream, False, scope, default_flags)
    if not stream.is_over():
        raise SyntaxError('unmatched ' + stream.current)
    return obj


def main():
    text = Char_stream(r'''{a: 12, b: 11, c: {b: 1, d: {a: 21}}, d1: ((c.d.a)*2+1), d2: 110, f1: func(1,2), f2: func1() }''')
    text = Char_stream(r'''{ c: {b: 1, d: {a: 21}}, d1: (((c.d).a)*2+1), f: (func)(1+1, 2*2) }''')
    # text = Char_stream('{a:1}')
    # text = Char_stream('{}')
    scope = {'func': lambda x,y: x+y, 'func1': lambda: print('hi!'),}

    obj = parse_object(text, scope)
    # snippet 9 - displaying your json data
    utils.export_json(obj)
    print(obj)

if __name__ == '__main__':
    main()
