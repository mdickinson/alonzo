# XXX To investigate: don't push None values onto value stack.
# XXX To investigate: use lookahead in more places, even when
#     not strictly necessary, to see if it can reduce the
#     number of states.

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
        return self._head.pop(0) if self._head else next(self._tail)

    def push(self, token):
        self._head.insert(0, token)

    def peek(self):
        token = self.next()
        self.push(token)
        return token

    def peek_type(self):
        token_type, token_value = self.peek()
        return token_type


# Shift states.
BEGIN = "BEGIN"
BEGIN_EXPR = "BEGIN_EXPR"
SLEFT = "LEFT"
SLEFT_EXPR = "LEFT_EXPR"
SLAMBDA = "LAMBDA"
SLAMBDA_EXPR = "LAMBDA_EXPR"
SSLASH = "SLASH"
SSLASH_NAMES = "SLASH_NAMES"

# Reduce states.
EXPR_ATOM = "EXPR_ATOM"
SLEFT_EXPR_RIGHT = "LEFT_EXPR_RIGHT"
SATOM = "ATOM"
SID = "SID"
SNAMES = "NAMES"
RLAMBDA = "RLAMBDA"
SNAMES_ID = "SNAMES_ID"

# Accept state.
BEGIN_EXPR_END = "BEGIN_EXPR_END"


class SMParser(object):
    """State-machine-based shift-reduce parser."""

    def parse(self, tokens):
        tokens = TokenStream(tokens)
        value_stack = []
        state_stack = []
        state = BEGIN

        def shift(next_state):
            state_stack.append(state)
            value_stack.append(token_value)
            return next_state

        while True:
            if state == BEGIN:
                token_type, token_value = tokens.next()
                if token_type == ID:
                    state = shift(SID)
                elif token_type == LEFT:
                    state = shift(SLEFT)
                elif token_type == RIGHT:
                    raise ParseError()
                elif token_type == SLASH:
                    state = shift(SSLASH)
                elif token_type == DOT:
                    raise ParseError()
                elif token_type == END:
                    raise ParseError()

                elif token_type == ATOM:
                    state = shift(SATOM)
                elif token_type == EXPR:
                    state = shift(BEGIN_EXPR)

                else:
                    raise NotImplementedError(
                        "token type {!r} in state {!r}".format(
                            token_type, state))

            elif state == BEGIN_EXPR:
                token_type, token_value = tokens.next()
                if token_type == ID:
                    state = shift(SID)
                elif token_type == LEFT:
                    state = shift(SLEFT)
                elif token_type == RIGHT:
                    raise ParseError()
                elif token_type == SLASH:
                    state = shift(SSLASH)
                elif token_type == DOT:
                    raise ParseError()
                elif token_type == END:
                    state = shift(BEGIN_EXPR_END)

                elif token_type == ATOM:
                    state = shift(EXPR_ATOM)

                else:
                    raise NotImplementedError(
                        "token type {!r} in state {!r}".format(
                            token_type, state))

            elif state == SLEFT:
                token_type, token_value = tokens.next()
                if token_type == ID:
                    state = shift(SID)
                elif token_type == LEFT:
                    state = shift(SLEFT)
                elif token_type == RIGHT:
                    raise ParseError()
                elif token_type == SLASH:
                    state = shift(SSLASH)
                elif token_type == DOT:
                    raise ParseError()
                elif token_type == END:
                    raise ParseError()

                elif token_type == ATOM:
                    state = shift(SATOM)
                elif token_type == EXPR:
                    state = shift(SLEFT_EXPR)

                else:
                    raise NotImplementedError(
                        "token type {!r} in state {!r}".format(
                            token_type, state))

            elif state == SLEFT_EXPR:
                token_type, token_value = tokens.next()
                if token_type == ID:
                    state = shift(SID)
                elif token_type == LEFT:
                    state = shift(SLEFT)
                elif token_type == RIGHT:
                    state = shift(SLEFT_EXPR_RIGHT)
                elif token_type == SLASH:
                    state = shift(SSLASH)
                elif token_type == DOT:
                    raise ParseError()
                elif token_type == END:
                    raise ParseError()

                elif token_type == ATOM:
                    state = shift(EXPR_ATOM)

                else:
                    raise NotImplementedError(
                        "token type {!r} in state {!r}".format(
                            token_type, state))

            elif state == SSLASH:
                token_type, token_value = tokens.next()
                if token_type == ID:
                    state = shift(SNAMES)
                elif token_type == LEFT:
                    raise ParseError()
                elif token_type == RIGHT:
                    raise ParseError()
                elif token_type == SLASH:
                    raise ParseError()
                elif token_type == DOT:
                    raise ParseError()
                elif token_type == END:
                    raise ParseError()

                elif token_type == NAMES:
                    state = shift(SSLASH_NAMES)

                else:
                    raise NotImplementedError(
                        "token type {!r} in state {!r}".format(
                            token_type, state))

            elif state == SSLASH_NAMES:
                token_type, token_value = tokens.next()
                if token_type == ID:
                    state = shift(SNAMES_ID)
                elif token_type == LEFT:
                    raise ParseError()
                elif token_type == RIGHT:
                    raise ParseError()
                elif token_type == SLASH:
                    raise ParseError()
                elif token_type == DOT:
                    state = shift(SLAMBDA)
                elif token_type == END:
                    raise ParseError()

                else:
                    raise NotImplementedError(
                        "token type {!r} in state {!r}".format(
                            token_type, state))

            elif state == SLAMBDA:
                token_type, token_value = tokens.next()
                if token_type == ID:
                    state = shift(SID)
                elif token_type == LEFT:
                    state = shift(SLEFT)
                elif token_type == RIGHT:
                    raise ParseError()
                elif token_type == SLASH:
                    state = shift(SSLASH)
                elif token_type == DOT:
                    raise ParseError()
                elif token_type == END:
                    raise ParseError()

                elif token_type == ATOM:
                    state = shift(SATOM)
                elif token_type == EXPR:
                    # Need lookahead!
                    if tokens.peek_type() in {END, RIGHT}:
                        state = shift(RLAMBDA)
                    else:
                        state = shift(SLAMBDA_EXPR)
                else:
                    raise NotImplementedError(
                        "token type {!r} in state {!r}".format(
                            token_type, state))

            elif state == SLAMBDA_EXPR:
                token_type, token_value = tokens.next()
                if token_type == ID:
                    state = shift(SID)
                elif token_type == LEFT:
                    state = shift(SLEFT)
                elif token_type == SLASH:
                    state = shift(SSLASH)
                elif token_type == DOT:
                    raise ParseError()
                # Not possible to have RIGHT or END here, since
                # we can only reach this state from SLAMBDA, after
                # lookahead.

                elif token_type == ATOM:
                    state = shift(EXPR_ATOM)

                else:
                    raise NotImplementedError(
                        "token type {!r} in state {!r}".format(
                            token_type, state))

            elif state == SNAMES_ID:
                # Reduce: names -> names ID
                state, state_stack = state_stack[-2], state_stack[:-2]
                values, value_stack = value_stack[-2:], value_stack[:-2]
                names, name = values
                names.append(name)
                tokens.push((NAMES, names))
            elif state == RLAMBDA:
                # Reduce: atom -> SLASH names DOT expr
                state, state_stack = state_stack[-4], state_stack[:-4]
                values, value_stack = value_stack[-4:], value_stack[:-4]
                _, names, _, atom = values
                while names:
                    atom = Function(names.pop(), atom)
                tokens.push((ATOM, atom))
            elif state == SNAMES:
                # Reduce: names -> ID
                state, state_stack = state_stack[-1], state_stack[:-1]
                value, value_stack = value_stack[-1], value_stack[:-1]
                names = [value]
                tokens.push((NAMES, names))
            elif state == SID:
                # Reduce: atom -> ID
                state, state_stack = state_stack[-1], state_stack[:-1]
                value, value_stack = value_stack[-1], value_stack[:-1]
                atom = Name(value)
                tokens.push((ATOM, atom))
            elif state == SATOM:
                # Reduce: expr -> atom
                state, state_stack = state_stack[-1], state_stack[:-1]
                value, value_stack = value_stack[-1], value_stack[:-1]
                expr = value
                tokens.push((EXPR, expr))
            elif state == EXPR_ATOM:
                # Reduce: expr -> expr atom
                state, state_stack = state_stack[-2], state_stack[:-2]
                values, value_stack = value_stack[-2:], value_stack[:-2]
                expr = Apply(values[0], values[1])
                tokens.push((EXPR, expr))
            elif state == SLEFT_EXPR_RIGHT:
                # Reduce: expr -> LEFT expr RIGHT
                state, state_stack = state_stack[-3], state_stack[:-3]
                value, value_stack = value_stack[-2], value_stack[:-3]
                atom = value
                tokens.push((ATOM, atom))

            elif state == BEGIN_EXPR_END:
                # Accept.
                expr, _ = value_stack
                return expr

            else:
                raise ValueError("Unknown state: {!r}".format(state))


def parse(s):
    tokens = tokenize(s)
    return SMParser().parse(tokens)


"""
Grammar

   names -> ID | names ID
   atom -> ID | LEFT expr RIGHT | SLASH names DOT expr
   expr -> atom | expr atom

"""
