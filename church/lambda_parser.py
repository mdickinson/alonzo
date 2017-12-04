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
        self._stack = []

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

    def shift(self):
        self._stack.append(self.next())

    def reduce_name(self):
        _, name = self._stack.pop()
        self._stack.append(Name(name))

    def reduce_parenthesized(self):
        self._stack.pop()
        expr = self._stack.pop()
        self._stack.pop()
        self._stack.append(expr)

    def reduce_apply(self):
        arg = self._stack.pop()
        function = self._stack.pop()
        self._stack.append(Apply(function, arg))

    def reduce_goal(self):
        self._stack.pop()
        expr = self._stack.pop()
        self._stack.append(expr)

    def parse_right(self):
        if self.peek() == RIGHT:
            self.shift()
        else:
            raise ParseError("Expected )")

    def parse_end(self):
        if self.peek() == END:
            self.shift()
        else:
            raise ParseError("Expected end of string")

    def parse_atom(self):
        if self.peek() == ID:
            self.shift()
            self.reduce_name()
        elif self.peek() == LEFT:
            self.shift()
            self.parse_expr()
            self.parse_right()
            self.reduce_parenthesized()
        else:
            raise ParseError()

    def parse_expr(self):
        self.parse_atom()
        self.parse_trailer()

    def parse_trailer(self):
        if self.peek() in {ID, LEFT}:
            self.parse_atom()
            self.reduce_apply()
            self.parse_trailer()

    def parse_goal(self):
        self.parse_expr()
        self.parse_end()
        self.reduce_goal()
        return self._stack.pop()


def parse(s):
    return Parser(tokenize(s)).parse_goal()


