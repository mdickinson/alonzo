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


class Function(object):
    def __init__(self, name, body):
        self.name = name
        self.body = body

    def __repr__(self):
        return "Function({!r}, {!r})".format(self.name, self.body)

    def __eq__(self, other):
        return (
            type(self) == type(other)
            and self.name == other.name
            and self.body == other.body
        )


# Token types: terminals
ID = "id"
LEFT = "left"
RIGHT = "right"
SLASH = "slash"
DOT = "dot"
END = "end"

# Token types: non-terminals
ATOM = "atom"
EXPR = "expr"
NAMES = "names"

IDENTIFIER_CHARACTERS = set(string.ascii_lowercase + "_")
WHITESPACE = set(" \n")
SINGLE_TOKEN_CHARS = {
    "(": LEFT,
    ")": RIGHT,
    "\\": SLASH,
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
        self._head = []

    def next(self):
        return self._head.pop() if self._head else next(self._tail)

    def push(self, token):
        self._head.append(token)


class SMParser(object):
    """State-machine-based shift-reduce parser."""

    def parse(self, tokens):
        tokens = TokenStream(tokens)
        value_stack = []
        state_stack = []
        state = 0

        def shift(next_state):
            state_stack.append(state)
            value_stack.append(token_value)
            return next_state

        while True:
            if state == 0:
                # Beginning of string; expect an expression.
                token_type, token_value = tokens.next()
                if token_type == ID:
                    state = shift(1)
                elif token_type == LEFT:
                    state = shift(2)
                elif token_type == SLASH:
                    state = shift(3)
                elif token_type == EXPR:
                    state = shift(4)
                elif token_type == ATOM:
                    state = shift(5)
                else:
                    raise ParseError()

            elif state == 1:
                # Reduce ID to ATOM
                state, state_stack = state_stack[-1], state_stack[:-1]
                value, value_stack = value_stack[-1], value_stack[:-1]
                atom = Name(value)
                tokens.push((ATOM, atom))

            elif state == 2:
                # After a LEFT: expect an expression.
                token_type, token_value = tokens.next()
                if token_type == ID:
                    state = shift(1)
                elif token_type == LEFT:
                    state = shift(2)
                elif token_type == SLASH:
                    state = shift(3)
                elif token_type == EXPR:
                    state = shift(6)
                elif token_type == ATOM:
                    state = shift(5)
                else:
                    raise ParseError()

            elif state == 3:
                # After a slash; expecting names.
                token_type, token_value = tokens.next()
                if token_type == ID:
                    state = shift(7)
                elif token_type == NAMES:
                    state = shift(8)
                else:
                    raise ParseError()

            elif state == 4:
                # BEGIN EXPR
                token_type, token_value = tokens.next()
                if token_type == END:
                    state = shift(9)
                elif token_type == ID:
                    state = shift(1)
                elif token_type == LEFT:
                    state = shift(2)
                elif token_type == SLASH:
                    state = shift(3)
                elif token_type == ATOM:
                    state = shift(10)
                else:
                    raise ParseError(
                        "Token of type {} in state {}".format(
                            token_type, state))

            elif state == 5:
                # Reduce: expr -> atom
                state, state_stack = state_stack[-1], state_stack[:-1]
                value, value_stack = value_stack[-1], value_stack[:-1]
                expr = value
                tokens.push((EXPR, expr))

            elif state == 6:
                token_type, token_value = tokens.next()
                if token_type == ID:
                    state = shift(1)
                elif token_type == LEFT:
                    state = shift(2)
                elif token_type == RIGHT:
                    state = shift(11)
                elif token_type == SLASH:
                    state = shift(3)
                elif token_type == ATOM:
                    state = shift(10)
                else:
                    raise ParseError()

            elif state == 7:
                # Reduce: names -> ID
                state, state_stack = state_stack[-1], state_stack[:-1]
                value, value_stack = value_stack[-1], value_stack[:-1]
                names = [value]
                tokens.push((NAMES, names))

            elif state == 8:
                token_type, token_value = tokens.next()
                if token_type == ID:
                    state = shift(12)
                elif token_type == DOT:
                    state = shift(13)
                else:
                    raise ParseError()

            elif state == 9:
                # accept
                return value_stack[-2]

            elif state == 10:
                # Reduce: expr -> expr atom
                state, state_stack = state_stack[-2], state_stack[:-2]
                values, value_stack = value_stack[-2:], value_stack[:-2]
                expr = Apply(values[0], values[1])
                tokens.push((EXPR, expr))

            elif state == 11:
                # Reduce: expr -> ( expr )
                state, state_stack = state_stack[-3], state_stack[:-3]
                value, value_stack = value_stack[-2], value_stack[:-3]
                atom = value
                tokens.push((ATOM, atom))

            elif state == 12:
                # Reduce: names -> names ID
                state, state_stack = state_stack[-2], state_stack[:-2]
                values, value_stack = value_stack[-2:], value_stack[:-2]
                names, name = values
                names.append(name)
                tokens.push((NAMES, names))

            elif state == 13:
                token_type, token_value = tokens.next()
                if token_type == ID:
                    state = shift(1)
                elif token_type == LEFT:
                    state = shift(2)
                elif token_type == SLASH:
                    state = shift(3)
                elif token_type == EXPR:
                    state = shift(14)
                elif token_type == ATOM:
                    state = shift(5)
                else:
                    raise ParseError()

            elif state == 14:
                # The interesting one: a mix of shift and reduce. This is
                # the one that needs lookahead.
                token_type, token_value = tokens.next()
                if token_type == ID:
                    state = shift(1)
                elif token_type == LEFT:
                    state = shift(2)
                elif token_type == SLASH:
                    state = shift(3)
                elif token_type == ATOM:
                    state = shift(10)
                else:
                    # push back! effectively, lookahead
                    tokens.push((token_type, token_value))
                    # Reduce: atom -> SLASH names DOT expr
                    state, state_stack = state_stack[-4], state_stack[:-4]
                    values, value_stack = value_stack[-4:], value_stack[:-4]
                    _, names, _, atom = values
                    while names:
                        atom = Function(names.pop(), atom)
                    tokens.push((ATOM, atom))

            else:
                raise ValueError("Unknown state: {!r}".format(state))


def parse(s):
    tokens = tokenize(s)
    return SMParser().parse(tokens)
