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


class RecursiveParser:
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


ATOM = "atom"
BEGIN = "begin"
EXPR = "expr"


class ShiftReduceParser(object):
    """Non-recursive shift-reduce parser for the lambda calculus.

    TODO: lambdas!
    """
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

    def matches(self, *types):
        if len(self._stack) < len(types):
            return False
        trailer = self._stack[len(self._stack) - len(types):]
        for token, type in zip(trailer, types):
            if token[0] != type:
                return False
        return True

    def parse(self):
        self._stack.append((BEGIN,))
        while True:
            if self.matches(ID):
                # Reduce: atom -> ID
                _, name = self._stack.pop()
                self._stack.append((ATOM, Name(name)))
            elif self.matches(LEFT, EXPR, RIGHT):
                # Reduce: LEFT expr RIGHT -> atom
                self._stack.pop()
                _, expr = self._stack.pop()
                self._stack.pop()
                self._stack.append((ATOM, expr))
            elif self.matches(EXPR, ATOM):
                # Reduce: expr -> expr atom
                _, arg = self._stack.pop()
                _, fn = self._stack.pop()
                self._stack.append((EXPR, Apply(fn, arg)))
            elif self.matches(ATOM):
                # Reduce: expr -> atom. Important that the
                # preceding rule takes precedence.
                _, expr = self._stack.pop()
                self._stack.append((EXPR, expr))
            elif self.matches(BEGIN, EXPR, END):
                self._stack.pop()
                _, expr = self._stack.pop()
                return expr
            elif self.matches(END):
                # Again, important that the preceding rule
                # takes precedence.
                raise ParseError()
            else:
                self._stack.append(self.next())


# Now convert to a state-based shift-reduce parser.
# States correspond to portions of the top of the stack.
"""
States and transitions (symbols are ID, LEFT, RIGHT, END)

BEGIN:
    LEFT -> shift to LEFT
    ID -> shift to BEGIN_EXPR
    RIGHT -> error
    END -> error
LEFT:
    LEFT -> shift to LEFT
    ID -> shift to LEFT_EXPR
    RIGHT -> error
    END -> error
BEGIN_EXPR:
    LEFT -> shift to LEFT
    ID -> reduce, back to BEGIN_EXPR
    RIGHT -> error
    END -> reduce, accept
LEFT_EXPR:
    LEFT -> shift to LEFT
    ID -> reduce, back to LEFT_EXPR
    RIGHT -> reduce, back to ... something
    END -> error

That seems to be it. What are we missing?

What's the ... something above? After we pop the (left, expr, right) from
the top of the stack and replace it with an expr, we're effectively pushing
another expr on whatever we had before. So we need a table entry for that ...

ex:

BEGIN -> BEGIN -> BEGIN -> BEGIN
         LEFT     LEFT     LEFT
                  ID       ID
                           RIGHT

...


expr = id | expr expr | (expr)

Rework. Missing rules are ParseErrors.

BEGIN:
    LEFT -> shift to LEFT
    ID -> shift to ID
    EXPR -> shift to BEGIN_EXPR
LEFT:
    LEFT -> shift to LEFT
    ID -> shift to ID
    EXPR -> shift to LEFT_EXPR
BEGIN_EXPR:
    LEFT -> shift to LEFT
    ID -> shift to ID
    EXPR -> shift to EXPR_EXPR
    END -> shift to BEGIN_EXPR_END
LEFT_EXPR:
    LEFT -> shift to LEFT
    ID -> shift to ID
    EXPR -> shift to EXPR_EXPR
    RIGHT -> shift to LEFT_EXPR_RIGHT

ID:
    reduce (expr -> id)
EXPR_EXPR:
    reduce (expr -> expr expr)
LEFT_EXPR_RIGHT:
    reduce (expr -> (expr) )
BEGIN_EXPR_END:
    accept

Need a token stack with push-back, though we only ever need one
token of push back.
"""


BEGIN_EXPR = (BEGIN, EXPR)
LEFT_EXPR = (LEFT, EXPR)
EXPR_EXPR = (EXPR, EXPR)
BEGIN_EXPR_END = (BEGIN, EXPR, END)
LEFT_EXPR_RIGHT = (LEFT, EXPR, END)


class SMParser(object):
    """State-machine-based shift-reduce parser."""
    def __init__(self, tokens):
        self._tokens = iter(tokens)
        self._peeked = None
        self._stack = [BEGIN]
        self._state_stack = [BEGIN]

    def next(self):
        """Get the next token."""
        if self._peeked is None:
            return next(self._tokens)
        else:
            token, self._peeked = self._peeked, None
            return token

    def push_back(self, token):
        if self._peeked is None:
            self._peeked = token
        else:
            raise ValueError("push back space already occupied")

    def pop(self, n):
        if n == 0:
            return []

        top = self._stack[-n:]
        del self._stack[-n:]
        del self._state_stack[-n:]
        return top

    def shift_to(self, next_state, token):
        self._stack.append(token)
        self._state_stack.append(next_state)

    def parse(self):
        while True:
            state = self._state_stack[-1]
            if state == BEGIN:
                next_token = self.next()
                if next_token[0] == LEFT:
                    self.shift_to(LEFT, next_token)
                elif next_token[0] == ID:
                    self.shift_to(ID, next_token)
                elif next_token[0] == EXPR:
                    self.shift_to(BEGIN_EXPR, next_token)
                else:
                    raise ParseError()
            elif state == LEFT:
                next_token = self.next()
                if next_token[0] == LEFT:
                    self.shift_to(LEFT, next_token)
                elif next_token[0] == ID:
                    self.shift_to(ID, next_token)
                elif next_token[0] == EXPR:
                    self.shift_to(LEFT_EXPR, next_token)
                else:
                    raise ParseError()
            elif state == BEGIN_EXPR:
                next_token = self.next()
                if next_token[0] == LEFT:
                    self.shift_to(LEFT, next_token)
                elif next_token[0] == ID:
                    self.shift_to(ID, next_token)
                elif next_token[0] == EXPR:
                    self.shift_to(EXPR_EXPR, next_token)
                elif next_token[0] == END:
                    self.shift_to(BEGIN_EXPR_END, next_token)
                else:
                    raise ParseError()
            elif state == LEFT_EXPR:
                next_token = self.next()
                if next_token[0] == LEFT:
                    self.shift_to(LEFT, next_token)
                elif next_token[0] == ID:
                    self.shift_to(ID, next_token)
                elif next_token[0] == EXPR:
                    self.shift_to(EXPR_EXPR, next_token)
                elif next_token[0] == RIGHT:
                    self.shift_to(LEFT_EXPR_RIGHT, next_token)
                else:
                    raise ParseError("Unexpected token: {!r}".format(
                        next_token))

            elif state == ID:
                (_, name), = self.pop(1)
                expr = Name(name)
                self.push_back((EXPR, expr))
            elif state == BEGIN_EXPR_END:
                (_, expr, _) = self.pop(3)
                return expr[1]
            elif state == EXPR_EXPR:
                fn, arg = self.pop(2)
                app = Apply(fn[1], arg[1])
                self.push_back((EXPR, app))
            elif state == LEFT_EXPR_RIGHT:
                (_, expr, _) = self.pop(3)
                self.push_back(expr)
            else:
                raise NotImplementedError("state: {!r}".format(state))


def parse(s):
    return SMParser(tokenize(s)).parse()
