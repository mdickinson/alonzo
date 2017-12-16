import string


# Classes providing the AST for the parsed expressions.

class LambdaAST(object):
    pass


class Apply(LambdaAST):
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


class Name(LambdaAST):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "Name({!r})".format(self.name)

    def __eq__(self, other):
        return (
            type(self) == type(other)
            and self.name == other.name
        )


class Function(LambdaAST):
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


SSTART = "start"
SLEFT = "left"
SDOT = "dot"

SSTART_EXPR = "start-expr"
SLEFT_EXPR = "left-expr"
SDOT_EXPR = "dot-expr"

SEXPR = "-expr"


def lambda_parser(tokens):
    """
    Parse a token stream into a lambda expression.
    """
    states = []
    state = SSTART
    values = []
    while True:
        token_type, token_value = tokens.next()
        if token_type == END and state == SSTART_EXPR:
            return values.pop()
        elif token_type == ID:
            tokens.push((ATOM, Name(token_value)))
        elif token_type in ATOM:
            if state in {SDOT, SLEFT, SSTART}:
                state += SEXPR
                values.append(token_value)
            else:
                values.append(Apply(values.pop(), token_value))
        elif token_type == LEFT:
            states.append(state)
            state = SLEFT
        elif token_type == SLASH:
            names = []
            while True:
                token_type, token_value = tokens.next()
                if token_type != ID:
                    break
                names.append(token_value)
            if names and token_type == DOT:
                values.append(names)
                states.append(state)
                state = SDOT
            else:
                raise ParseError()
        elif token_type == RIGHT and state == SLEFT_EXPR:
            state = states.pop()
            tokens.push((ATOM, values.pop()))
        elif state == SDOT_EXPR:
            state = states.pop()
            atom, names = values.pop(), values.pop()
            while names:
                atom = Function(names.pop(), atom)
            tokens.push((token_type, token_value))
            tokens.push((ATOM, atom))
        else:
            raise ParseError("Unexpected token {!r} in state {!r}".format(
                token_type, state))


def parse(s):
    return lambda_parser(TokenStream(tokenize(s)))
