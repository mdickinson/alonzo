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


# Token types: terminals and non-terminals.
ATOM = "atom"
DOT = "dot"
END = "end"
ID = "id"
LEFT = "left"
RIGHT = "right"
SLASH = "slash"

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


class ParseSuccess(Exception):
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

    def __iter__(self):
        return self

    def __next__(self):
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


TOKEN_TYPES = [ATOM, DOT, END, ID, LEFT, RIGHT, SLASH]

parse_expr_methods = {
    token_type: "parse_expr_{}".format(token_type)
    for token_type in TOKEN_TYPES
}


class LambdaParser(object):
    def __init__(self, tokens):
        self.state, self.states, self.values = SSTART, [], []
        self.tokens = tokens

    def reduce_atom_from_lambda(self):
        self.tokens.push(self.token)
        body, names = self.values.pop(), self.values.pop()
        while names:
            body = Function(names.pop(), body)
        self.tokens.push((ATOM, body))
        self.state = self.states.pop()

    def parse_names(self):
        """
        Parse sequence of parameter names following a lambda.
        """
        names = []
        while True:
            token_type, token_value = next(self.tokens)
            if token_type != ID:
                break
            names.append(token_value)
        if not names or token_type != DOT:
            raise ParseError("Invalid name sequence")
        self.values.append(names)

    def parse_expr_id(self):
        token_type, token_value = self.token
        self.tokens.push((ATOM, Name(token_value)))

    def parse_expr_atom(self):
        token_type, token_value = self.token
        if self.state.endswith(SEXPR):
            self.values.append(Apply(self.values.pop(), token_value))
        else:
            self.values.append(token_value)
            self.state += SEXPR

    def parse_expr_left(self):
        self.states.append(self.state)
        self.state = SLEFT

    def parse_expr_slash(self):
        self.parse_names()
        self.states.append(self.state)
        self.state = SDOT

    def parse_expr_end(self):
        if self.state == SSTART_EXPR:
            raise ParseSuccess()
        elif self.state == SDOT_EXPR:
            self.reduce_atom_from_lambda()
        else:
            raise ParseError("Unexpected end of input")

    def parse_expr_right(self):
        if self.state == SLEFT_EXPR:
            self.state = self.states.pop()
            self.tokens.push((ATOM, self.values.pop()))
        elif self.state == SDOT_EXPR:
            self.reduce_atom_from_lambda()
        else:
            raise ParseError("Unexpected token: ')'")

    def parse_expr_dot(self):
        raise ParseError("Unexpected token: '.'")

    def parse_expr(self):
        """
        Parse a token stream into a lambda expression.
        """
        try:
            while True:
                token_type, token_value = self.token = next(self.tokens)
                getattr(self, parse_expr_methods[token_type])()
        except ParseSuccess:
            return self.values.pop()


def parse(s):
    return LambdaParser(TokenStream(tokenize(s))).parse_expr()
