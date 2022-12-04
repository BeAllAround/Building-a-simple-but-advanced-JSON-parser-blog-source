#!/usr/bin/python3
import sys
import utils
from parser import Token_stream # our library for lexical analysis/tokenization

def skip_space(token_stream: Token_stream):
    while not token_stream.is_over() and (token_stream == ' ' or token_stream == '\n'):
        token_stream.next_char()

def parse_tem(token_stream: Token_stream, get: bool):
    if get:
        token_stream.next_char()
    value = ''
    if not token_stream.current.isalpha():
        raise SyntaxError("Expected a template to start with an alpha")
    while token_stream.current.isalpha() or token_stream.current.isdigit():
        value += token_stream.current
        token_stream.next_char()
    return value

def expr(token_stream: Token_stream, get: bool, scope: dict, flags: utils.Map):
    left = term(token_stream, get, scope, flags)

    while True:
        if token_stream == '+':
            left += term(token_stream, True, scope, flags)
        elif token_stream == '-':
            left -= term(token_stream, True, scope, flags)
        else:
            return left

def term(token_stream: Token_stream, get: bool, scope: dict, flags: utils.Map):
    left = prim(token_stream, get, scope, flags)

    while True:
        if token_stream == '*':
            left *= prim(token_stream, True, scope, flags)
        elif token_stream == '/':
            left /= prim(token_stream, True, scope, flags)
        else:
            return left

def prim(token_stream: Token_stream, get: bool, scope: dict, flags: utils.Map):
    if get:
        token_stream.next_char()
    skip_space(token_stream)
    if token_stream == '(':
        value = expr(token_stream, True, scope, flags)
        value_ptr = [value]
        if token_stream != ')':
            raise SyntaxError("Missing ')'")
        token_stream.next_char() # eat ')'
        skip_space(token_stream)
        chain_main(token_stream, value_ptr, scope)
        value = value_ptr[0]
        return value

    return parse_obj_and_chain(token_stream, False, scope, flags) # use the complete variant of parse_obj supporting method chaining

def chain_main(token_stream: Token_stream, value_ptr: list, scope: dict):
    while True:
        if callable(value_ptr[0]) and token_stream == '(':
            args = [] # a variable to store the evaluated arguments

            ts = Token_stream(token_stream.source, token_stream.c)
            token_stream.next_char()
            skip_space(token_stream)
            if token_stream == ')':
                token_stream.next_char() # eat ')'
                skip_space(token_stream)
                value_ptr[0] = value_ptr[0]() # evaluate the function with no arguments passed
                continue
            else:
                token_stream.set_ts(ts) # reset the token stream to last matched '('

            while True:
                args.append(expr(token_stream, True, scope, utils.Map({'temFlag': True, 'isKey': False,})))
                if token_stream == ',':
                    continue
                elif token_stream == ')':
                    token_stream.next_char()
                    skip_space(token_stream)
                    value_ptr[0] = value_ptr[0](*args) # evaluate the function with x number of arguments passed
                    break
                else:
                    raise SyntaxError("Unexpected token while parsing a function: " + token_stream.current)
        elif type(value_ptr[0]) == dict and token_stream == '.':
            tem = parse_tem(token_stream, True)
            skip_space(token_stream)
            value_ptr[0] = value_ptr[0][tem]
            continue

        else:
            break


def parse_obj_and_chain(token_stream: Token_stream, get: bool, scope: dict, flags: utils.Map):
    value = parse_obj(token_stream, get, scope, flags)
    value_ptr = [value]
    chain_main(token_stream, value_ptr, scope)
    return value_ptr[0]

def parse_obj(token_stream: Token_stream, get: bool, scope: dict, flags: utils.Map):
    if get:
        token_stream.next_char()

    skip_space(token_stream)

    if token_stream.current.isdigit():
        token = ''
        while token_stream.current.isdigit():
            token += token_stream.current
            token_stream.next_char()
        skip_space(token_stream)
        return int(token, 10) # base 10

    elif token_stream.current.isalpha() and flags.temFlag:
        tem = parse_tem(token_stream, False)
        skip_space(token_stream)

        # print('flags: ', tem, flags)

        if flags.isKey:
            return tem

        if tem not in scope.keys():
            raise NameError(tem + " not defined")
        return scope[tem]

    elif token_stream == '{':
        obj = {}
        obj_scope = {}
        ts = Token_stream(token_stream.source, token_stream.c)
        token_stream.next_char()
        skip_space(token_stream)
        if token_stream == '}':
            token_stream.next_char() # eat '}'
            skip_space(token_stream)
            return obj
        else:
            token_stream.set_ts(ts) # reset the token stream back to last '{' and proceed with the parsing

        utils.deep_update(obj_scope, scope)
        
        while True:
            key = parse_obj(token_stream, True, scope, utils.Map({'temFlag': True, 'isKey': True,}))
            # print('key: ', key)
            if token_stream == ':':
                value = expr(token_stream, True, obj_scope, utils.Map({'temFlag': True, 'isKey': False,}))
                utils.deep_update(obj_scope, {key: value})
                utils.deep_update(obj, {key: value})

                if token_stream == '}':
                    token_stream.next_char() # eat '}'
                    skip_space(token_stream)
                    return obj
                elif token_stream == ',':
                    continue
                else:
                    print([token_stream.current])
                    raise SyntaxError("Unexpected token " + token_stream.current)
    else:
        raise SyntaxError("Unexpected token " + token_stream.current)

def main():
    text = Token_stream(r'''{a: 12, b: 11, c: {b: 1, d: {a: 21}}, d1: ((c.d.a)*2+1), d2: 110, f1: func(1,2), f2: func1() }''')
    text = Token_stream(r'''{c: {b: 1, d: {a: 21}}, d1: (((c.d).a)*2+1), f: (func)(1+1, 2*2)}''')
    # text = Token_stream('{a:1}')
    # text = Token_stream('{}')
    scope = {'func': lambda x,y: x+y, 'func1': lambda: print('hi!'),}
    default_flags = {}
    obj = parse_obj(text, False, scope, default_flags)
    # snippet 9 - displaying your json data
    utils.export_json(obj)
    print(obj)

if __name__ == '__main__':
    main()
