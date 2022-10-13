#!/usr/bin/python3
import sys
import utils
from token import Token

def skip_space(token: Token):
    while not token.is_over() and (token == ' ' or token == '\n'):
        token.next_token()

def parse_tem(token: Token, get: bool):
    if get:
        token.next_token()
    value = ''
    if not token.current.isalpha():
        raise SyntaxError("Expected a template to start with an alpha")
    while token.current.isalpha() or token.current.isdigit():
        value += token.current
        token.next_token()
    return value

def expr(token: Token, get: bool, scope: dict, flags: utils.Map):
    left = term(token, get, scope, flags)

    while True:
        if token == '+':
            left += term(token, True, scope, flags)
        elif token == '-':
            left -= term(token, True, scope, flags)
        else:
            return left

def term(token: Token, get: bool, scope: dict, flags: utils.Map):
    left = prim(token, get, scope, flags)

    while True:
        if token == '*':
            left *= prim(token, True, scope, flags)
        elif token == '/':
            left /= prim(token, True, scope, flags)
        else:
            return left

def prim(token: Token, get: bool, scope: dict, flags: utils.Map):
    if get:
        token.next_token()
    skip_space(token)
    if token == '(':
        value = expr(token, True, scope, flags)
        value_ptr = [value]
        if token != ')':
            raise SyntaxError("Missing ')'")
        token.next_token() # eat ')'
        skip_space(token)
        chain_main(token, value_ptr, scope)
        value = value_ptr[0]
        return value

    return parse_obj_and_chain(token, False, scope, flags) # use the complete variant of parse_obj supporting method chaining

def chain_main(token: Token, value_ptr: list, scope: dict):
    while True:
        if callable(value_ptr[0]) and token == '(':
            args = [] # a variable to store the parsed values

            t = Token(token.source, token.c)
            token.next_token()
            skip_space(token)
            if token == ')':
                token.next_token() # eat ')'
                skip_space(token)
                value_ptr[0] = value_ptr[0]() # evaluate the function with no arguments passed
                continue
            else:
                token.set_token(t) # reset the current token to last matched '('

            while True:
                args.append(expr(token, True, scope, utils.Map({'temFlag': True, 'isKey': False,})))
                if token == ',':
                    continue
                elif token == ')':
                    token.next_token()
                    skip_space(token)
                    value_ptr[0] = value_ptr[0](*args) # evaluate the function with x number of arguments passed
                    break
                else:
                    raise SyntaxError("Unexpected token while parsing a function: " + token.current)
        elif type(value_ptr[0]) == dict and token == '.':
            tem = parse_tem(token, True)
            skip_space(token)
            value_ptr[0] = value_ptr[0][tem]
            continue

        else:
            break


def parse_obj_and_chain(token: Token, get: bool, scope: dict, flags: utils.Map):
    value = parse_obj(token, get, scope, flags)
    value_ptr = [value]
    chain_main(token, value_ptr, scope)
    return value_ptr[0]

def parse_obj(token: Token, get: bool, scope: dict, flags: utils.Map):
    if get:
        token.next_token()

    skip_space(token)

    if token.current.isdigit():
        value = ''
        while token.current.isdigit():
            value += token.current
            token.next_token()
        skip_space(token)
        return int(value, 10) # base 10

    elif token.current.isalpha() and flags.temFlag:
        tem = parse_tem(token, False)
        skip_space(token)

        # print('flags: ', tem, flags)

        if flags.isKey:
            return tem

        if tem not in scope.keys():
            raise NameError(tem + " not defined")
        return scope[tem]

    elif token == '{':
        obj = {}
        obj_scope = {}
        t = Token(token.source, token.c)
        token.next_token()
        skip_space(token)
        if token == '}':
            token.next_token() # eat '}'
            skip_space(token)
            return obj
        else:
            token.set_token(t) # reset the current token back to last '{' and proceed with the parsing

        utils.deep_update(obj_scope, scope)
        
        while True:
            key = parse_obj(token, True, scope, utils.Map({'temFlag': True, 'isKey': True,}))
            # print('key: ', key)
            if token == ':':
                value = expr(token, True, obj_scope, utils.Map({'temFlag': True, 'isKey': False,}))
                utils.deep_update(obj_scope, {key: value})
                utils.deep_update(obj, {key: value})

                if token == '}':
                    token.next_token() # eat '}'
                    skip_space(token)
                    return obj
                elif token == ',':
                    continue
                else:
                    print([token.current])
                    raise SyntaxError("Unexpected token " + token.current)
    else:
        raise SyntaxError("Unexpected token " + token.current)

def main():
    t = Token(r'''{a: 12, b: 11, c: {b: 1, d: {a: 21}}, d1: ((c.d.a)*2+1), d2: 110, f1: func(1,2), f2: func1() }''')
    t = Token(r'''{c: {b: 1, d: {a: 21}}, d1: (((c.d).a)*2+1), f: (func)(1+1, 2*2)}''')
    # t = Token('{a:1}')
    # t = Token('{}')
    scope = {'func': lambda x,y: x+y, 'func1': lambda: print('hi!'),}
    default_flags = {}
    print(parse_obj(t, False, scope, default_flags))

if __name__ == '__main__':
    main()
