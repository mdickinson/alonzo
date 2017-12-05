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


class TokenStream(object):
    """
    Token stream, with a single push-back slot.
    """
    def __init__(self, tokens):
        self._tail = iter(tokens)
        # We assume that `None` is not a valid token.
        self._head = None

    def next(self):
        if self._head is None:
            token = next(self._tail)
        else:
            token, self._head = self._head, None
        return token

    def push(self, token):
        if self._head is None:
            self._head = token
        else:
            raise ValueError("no space to push")


class SMParser(object):
    """State-machine-based shift-reduce parser."""
    def __init__(self, transitions, reductions, initial_state, accept_state):
        self.transitions = transitions
        self.reductions = reductions
        self.accept_state = accept_state
        self.initial_state = initial_state

    def parse(self, tokens):
        tokens = TokenStream(tokens)
        value_stack = []
        state_stack = []
        state = self.initial_state
        while state != self.accept_state:
            if state in self.transitions:
                token_type, token_value = tokens.next()
                try:
                    next_state = self.transitions[state][token_type]
                except KeyError:
                    raise ParseError()
                value_stack.append(token_value)
                state_stack.append(state)
                state = next_state
            elif state in self.reductions:
                count, type, reducer = self.reductions[state]
                args, value_stack = value_stack[-count:], value_stack[:-count]
                state, state_stack = state_stack[-count], state_stack[:-count]
                token = type, reducer(*args)
                tokens.push(token)
            else:
                raise RuntimeError("Unknown state: {!r}".format(state))
        return value_stack.pop()


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


parser = SMParser(
    transitions=transitions,
    reductions=reductions,
    initial_state=BEGIN,
    accept_state=ACCEPT,
)


def parse(s):
    return parser.parse(tokenize(s))
