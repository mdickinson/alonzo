"""

First: without lambdas.

Terminals: ID, LEFT, RIGHT

atom = ID | LEFT expr RIGHT
expr = atom | expr atom

"""
import string


class Apply(object):
    def __init__(self, function, argument):
        self.function = function
        self.argument = argument

    def __repr__(self):
        return "Apply({!r}, {!r})".format(self.function, self.argument)

    def __eq__(self, other):
        return (
            type(self) == type(other)
            and self.function == other.function
            and self.argument == other.argument
        )


class Name(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "Name({!r})".format(self.name)

    def __eq__(self, other):
        return (
            type(self) == type(other)
            and self.name == other.name
        )


ID = "id"
LEFT = "left"
RIGHT = "right"
LAMBDA = "lambda"
DOT = "dot"
END = "end"

IDENTIFIER_CHARACTERS = set(string.ascii_lowercase + "_")
WHITESPACE = set(" \n")
SINGLE_TOKEN_CHARS = {
    "(": LEFT,
    ")": RIGHT,
    "\\": LAMBDA,
    ".": DOT,
}


class ParseError(Exception):
    pass


def tokenize(s):
    chars = iter(s)
    # Our tokenizer is a finite state machine with just two states: either
    # we're parsing an identifier, or we're not.
    parsing_id = False
    while True:
        c = next(chars, None)
        if c in IDENTIFIER_CHARACTERS:
            if not parsing_id:
                parsing_id = True
                id_chars = []
            id_chars.append(c)
        else:
            if parsing_id:
                yield ID, ''.join(id_chars)
                parsing_id = False
            if c in SINGLE_TOKEN_CHARS:
                yield SINGLE_TOKEN_CHARS[c],
            elif c in WHITESPACE:
                pass
            elif c is None:
                yield END,
                break
            else:
                raise ParseError("Invalid character in string: {}".format(c))


class Parser:
    def __init__(self, tokens):
        self._tokens = iter(tokens)
        self._peeked = None

    def peek(self):
        """Return type of the next token, without consuming it."""
        if self._peeked is None:
            self._peeked = next(self._tokens)
        return self._peeked[0]

    def next(self):
        """Get the next token."""
        self.peek()
        token, self._peeked = self._peeked, None
        return token

    def parse_atom(self):
        if self.peek() == ID:
            token = self.next()
            return Name(token[1])
        elif self.peek() == LEFT:
            self.next()
            expr = self.parse_expr()
            self.next()
            return expr
        else:
            raise ParseError()

    def parse_expr(self):
        head = self.parse_atom()
        while True:
            if self.peek() in {ID, LEFT}:
                arg = self.parse_atom()
                head = Apply(head, arg)
            else:
                break
        return head

    def parse_goal(self):
        expr = self.parse_expr()
        if self.peek() in {END}:
            self.next()
        return expr


def parse(s):
    return Parser(tokenize(s)).parse_goal()


def test_parse_simple_expressions():
    w, x, y, z = map(Name, "wxyz")
    assert parse("x") == x
    assert parse("x y") == Apply(x, y)
    assert parse("x (y)") == Apply(x, y)
    assert parse("(x) y") == Apply(x, y)
    assert parse("(x)") == x
    assert parse("((x))") == x
    assert parse("x y z") == Apply(Apply(x, y), z)
    assert parse("(x y) z") == Apply(Apply(x, y), z)
    assert parse("x (y z)") == Apply(x, Apply(y, z))
    assert parse("w x y z") == Apply(Apply(Apply(w, x), y), z)
    assert parse("(w x)(y z)") == Apply(Apply(w, x), Apply(y, z))


test_parse_simple_expressions()
