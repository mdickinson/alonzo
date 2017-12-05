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
    """
    Tokenize the string, generating a stream of pairs
    of the form (token_type, token_value).
    """
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
                yield SINGLE_TOKEN_CHARS[c], None
            elif c in WHITESPACE:
                pass
            elif c is None:
                yield END, None
                break
            else:
                raise ParseError("Invalid character in string: {}".format(c))


BEGIN = "begin"
EXPR = "expr"
GOAL = "goal"

"""
States and transitions (symbols are ID, LEFT, RIGHT, END, EXPR)

BEGIN:
    LEFT -> shift to LEFT
    ID -> shift to ID
    EXPR -> shift to BEGIN_EXPR
    GOAL -> shift to ACCEPT
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
    reduce (goal -> expr END)

Need a token stack with push-back, though we only ever need one
token of push back.
"""

ACCEPT = "accept"
BEGIN_EXPR = (BEGIN, EXPR)
LEFT_EXPR = (LEFT, EXPR)
EXPR_EXPR = (EXPR, EXPR)
BEGIN_EXPR_END = (BEGIN, EXPR, END)
LEFT_EXPR_RIGHT = (LEFT, EXPR, END)

# Transition table for shift states.
transitions = {
    BEGIN: {LEFT: LEFT, ID: ID, EXPR: BEGIN_EXPR, GOAL: ACCEPT},
    LEFT: {LEFT: LEFT, ID: ID, EXPR: LEFT_EXPR},
    BEGIN_EXPR: {LEFT: LEFT, ID: ID, EXPR: EXPR_EXPR, END: BEGIN_EXPR_END},
    LEFT_EXPR: {LEFT: LEFT, ID: ID, EXPR: EXPR_EXPR, RIGHT: LEFT_EXPR_RIGHT},
}

# Reduction states: each state maps to the number of values it
# consumes followed by the type of token produced by the reduction
# and the function.
reductions = {
    ID: (1, EXPR, Name),
    EXPR_EXPR: (2, EXPR, Apply),
    LEFT_EXPR_RIGHT: (3, EXPR, lambda x, y, z: y),
    BEGIN_EXPR_END: (2, GOAL, lambda x, y: x),
}


class SMParser(object):
    """State-machine-based shift-reduce parser."""
    def __init__(self, tokens):
        self._tokens = iter(tokens)
        self._peeked = None
        self._value_stack = []
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
        top = self._value_stack[-n:]
        del self._value_stack[-n:]
        del self._state_stack[-n:]
        return top

    def shift_to(self, next_state, token):
        self._value_stack.append(token)
        self._state_stack.append(next_state)

    def reduce_id(self, id):
        return Name(id)

    def reduce_apply(self, fn, arg):
        return Apply(fn, arg)

    def reduce_parenthesized(self, left, expr, right):
        return expr

    def parse(self):
        while True:
            state = self._state_stack[-1]
            if state in transitions:
                token_type, token_value = self.next()
                try:
                    next_state = transitions[state][token_type]
                except KeyError:
                    raise ParseError()
                self.shift_to(next_state, token_value)
            elif state in reductions:
                count, type, reducer = reductions[state]
                self.push_back((type, reducer(*self.pop(count))))
            elif state == ACCEPT:
                return self._value_stack.pop()
            else:
                raise AssertionError("Shouldn't ever get here.")


def parse(s):
    return SMParser(tokenize(s)).parse()
