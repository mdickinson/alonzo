import enum

from church.token import (
    END_TOKEN,
    ID_TOKEN,
    SINGLE_CHAR_TOKEN,
    Token,
    TokenType,
)


# Classes providing the AST for the parsed expressions.

class AST(object):
    def __eq__(self, other):
        # Non-recursive equality check.
        to_compare = [(self, other)]
        while to_compare:
            expr0, expr1 = to_compare.pop()
            if type(expr0) != type(expr1):
                return False
            elif isinstance(expr0, Name):
                if expr0.name != expr1.name:
                    return False
            elif isinstance(expr0, Function):
                if expr0.name != expr1.name:
                    return False
                to_compare.append((expr0.body, expr1.body))
            elif isinstance(expr0, Apply):
                to_compare.append((expr0.argument, expr1.argument))
                to_compare.append((expr0.function, expr1.function))
            else:
                return False
        return True


class Apply(AST):
    def __init__(self, function, argument):
        self.function = function
        self.argument = argument

    def __repr__(self):
        return "Apply({!r}, {!r})".format(self.function, self.argument)


class Name(AST):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "Name({!r})".format(self.name)


class Function(AST):
    def __init__(self, name, body):
        self.name = name
        self.body = body

    def __repr__(self):
        return "Function({!r}, {!r})".format(self.name, self.body)


#: Extra non-terminal token type.
ATOM = "atom"


class ParseError(Exception):
    pass


class ParseSuccess(Exception):
    pass


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


PARSE_EXPR_METHODS = {
    TokenType.ID: "parse_expr_id",
    TokenType.LEFT: "parse_expr_left",
    TokenType.RIGHT: "parse_expr_right",
    TokenType.SLASH: "parse_expr_slash",
    TokenType.DOT: "parse_expr_dot",
    TokenType.END: "parse_expr_end",
    ATOM: "parse_expr_atom",
}


def ATOM_TOKEN(expr):
    return Token(ATOM, expr)


class LambdaParser(object):
    def __init__(self, tokens):
        self.state, self.states, self.values = SSTART, [], []
        self.tokens = tokens

    def reduce_atom_from_lambda(self):
        self.tokens.push(self.token)
        body, names = self.values.pop(), self.values.pop()
        while names:
            body = Function(names.pop(), body)
        self.tokens.push(ATOM_TOKEN(body))
        self.state = self.states.pop()

    def parse_names(self):
        """
        Parse sequence of parameter names following a lambda.
        """
        names = []
        while True:
            token = next(self.tokens)
            if token.type != TokenType.ID:
                break
            names.append(token.value)
        if not names or token.type != TokenType.DOT:
            raise ParseError("Invalid name sequence")
        self.values.append(names)

    def parse_expr_id(self):
        self.tokens.push(ATOM_TOKEN(Name(self.token.value)))

    def parse_expr_atom(self):
        token = self.token
        if self.state.endswith(SEXPR):
            self.values.append(Apply(self.values.pop(), token.value))
        else:
            self.values.append(token.value)
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
            self.tokens.push(ATOM_TOKEN(self.values.pop()))
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
                token = self.token = next(self.tokens)
                getattr(self, PARSE_EXPR_METHODS[token.type])()
        except ParseSuccess:
            return self.values.pop()


def parse(tokens):
    return LambdaParser(TokenStream(tokens)).parse_expr()


class UnparseState(enum.Enum):
    """
    States used by unparse.
    """
    TOP = enum.auto()
    LEADING = enum.auto()
    TRAILING = enum.auto()
    MIDDLE = enum.auto()
    WRITE_LEFT = enum.auto()
    WRITE_RIGHT = enum.auto()


#: Map from old to new state for Function arguments.
ARGUMENT_STATE = {
    UnparseState.TOP: UnparseState.TRAILING,
    UnparseState.LEADING: UnparseState.MIDDLE,
}


def unparse(expr):
    """
    Unparse an expr into a sequence of tokens.
    """
    # to_do maintains a list of (state, expr) pairs.
    # For some states, the corresponding expr is None.
    to_do = [(UnparseState.TOP, expr)]
    while to_do:
        state, expr = to_do.pop()
        if state == UnparseState.WRITE_RIGHT:
            yield SINGLE_CHAR_TOKEN[")"]
        elif state == UnparseState.WRITE_LEFT:
            yield SINGLE_CHAR_TOKEN["("]
        elif type(expr) == Name:
            yield ID_TOKEN(expr.name)
        elif type(expr) == Apply:
            if state in ARGUMENT_STATE:
                to_do.append((ARGUMENT_STATE[state], expr.argument))
                to_do.append((UnparseState.LEADING, expr.function))
            else:
                to_do.append((UnparseState.WRITE_RIGHT, None))
                to_do.append((UnparseState.TOP, expr))
                to_do.append((UnparseState.WRITE_LEFT, None))
        elif type(expr) == Function:
            if state in {UnparseState.TOP, UnparseState.TRAILING}:
                body, names = expr, []
                while type(body) == Function:
                    names.append(body.name)
                    body = body.body
                to_do.append((UnparseState.TOP, body))
                yield SINGLE_CHAR_TOKEN["\\"]
                yield from (ID_TOKEN(name) for name in names)
                yield SINGLE_CHAR_TOKEN["."]
            else:
                to_do.append((UnparseState.WRITE_RIGHT, None))
                to_do.append((UnparseState.TOP, expr))
                to_do.append((UnparseState.WRITE_LEFT, None))
        else:
            assert False, "should never get here"
    yield END_TOKEN
