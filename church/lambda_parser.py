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

        def go_to(next_state):
            nonlocal state
            state_stack.append(state)
            state = next_state

        while True:
            token_type, token_value = tokens.next()
            if token_type in {ID, ATOM}:
                if token_type == ID:
                    token_value = Name(token_value)
                value_stack.append(token_value)
                if state in {0, 2, 13}:
                    tokens.push((EXPR, value_stack.pop()))
                else:
                    state = state_stack.pop()
                    arg = value_stack.pop()
                    fn = value_stack.pop()
                    tokens.push((EXPR, Apply(fn, arg)))
            elif token_type == LEFT:
                go_to(2)
            elif token_type == SLASH:
                names = []
                while True:
                    token_type, token_value = tokens.next()
                    if token_type != ID:
                        break
                    names.append(token_value)
                if names and token_type == DOT:
                    value_stack.append(names)
                    go_to(13)
                else:
                    raise ParseError()
            elif state in {0, 2, 13} and token_type == EXPR:
                value_stack.append(token_value)
                go_to({0: 4, 2: 6, 13: 14}[state])
            elif state == 4 and token_type == END:
                return value_stack.pop()
            elif state == 6 and token_type == RIGHT:
                state_stack.pop()
                state = state_stack.pop()
                tokens.push((ATOM, value_stack.pop()))
            elif state == 14:
                state_stack.pop()
                state = state_stack.pop()
                atom = value_stack.pop()
                names = value_stack.pop()
                while names:
                    atom = Function(names.pop(), atom)
                tokens.push((token_type, token_value))
                tokens.push((ATOM, atom))
            else:
                raise ParseError()


def parse(s):
    tokens = tokenize(s)
    return SMParser().parse(tokens)
