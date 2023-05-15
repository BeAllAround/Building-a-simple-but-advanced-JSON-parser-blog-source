#!/usr/bin/python3

import unittest

from parser import CharStream
from main import interpret_object


def interpret(text: str, ctx: dict = {}):
    out = interpret_object(CharStream(text), ctx)
    return out

class TestLanguage(unittest.TestCase):
    def __init__(self, *args):
        super().__init__(*args)
        self.ctx = {}

    def test_foo_object(self):
        foo = interpret('{foo: 1}', self.ctx)
        self.assertEqual(str(foo), "{'foo': 1}")

    def test_empty_object(self):
        empty = interpret('{}', self.ctx)
        self.assertEqual(str(empty), '{}')

    def test_nested_object(self):
        nested = interpret('{foo:{zoo: {}}}', self.ctx)
        self.assertEqual(str(nested), "{'foo': {'zoo': {}}}")

    def test_nested_merge(self):
        text = r'''
            {
              foo: { zoo: { a:1 } },
              foo: { zoo: { b:2 } }
            }
        '''
        expected = "{'foo': {'zoo': {'a': 1, 'b': 2}}}"
        nested_merge = interpret(text, self.ctx)
        self.assertEqual(str(nested_merge), expected)

    def test_object_expression(self):
        text = '{ foo: (1+1)*10 }'
        expression = interpret(text, self.ctx)
        self.assertEqual(str(expression), "{'foo': 20}")

    def test_object_chainable(self):
        text = r'''
          {
            foo: { b: 1 },
            boo: foo.b
          }
        '''
        expected = "{'foo': {'b': 1}, 'boo': 1}"
        chainable = interpret(text, self.ctx)
        self.assertEqual(str(chainable), expected)

def unit_test():
    unittest.main()


if __name__ == '__main__':
    unit_test()
