# XXX Top-level function to tokenize *and* parse: users of ast
# should be able to use it without needing to dig into token.py.

# XXX Fix docstring for flatten.

# XXX Get rid of use of enum.
"""
Abstract syntax tree representation of a lambda expression.

At this level, we don't deal with name binding; names
are simply strings.
"""
import enum

from church.token import (
    END_TOKEN,
    ID_TOKEN,
    SINGLE_CHAR_TOKEN,
    Token,
)


# Classes providing the AST for the parsed expressions.
AstToken = enum.Enum(
    "AstToken",
    "NAME OPEN_FUNCTION CLOSE_FUNCTION OPEN_APPLY CLOSE_APPLY"
    " OPEN_DEFINITION DEFINITION_ARGS"
)


class Ast:
    def flatten(self):
        """
        # XXX Update this description! And do away with the
        # unnecessary use of enum.

        Flatten an AST expression into a series of tokens.

        Useful for recursion-free equality testing, representation
        and binding operations.

        Generates a sequence of pairs. Each pair is of the form:

        - (NAME, <name>)
        - (OPEN_FUNCTION, <name>)
        - (CLOSE_FUNCTION, None)
        - (OPEN_APPLY, None)
        - (CLOSE_APPLY, None)

        """
        to_do = [("PROCESS", self)]
        while to_do:
            action, arg = to_do.pop()
            if action == "PROCESS":
                to_do.extend(reversed(arg._pieces()))
            elif action == "YIELD":
                yield arg
            else:
                raise RuntimeError("Unexpected action: {!r}".format(action))

    def __eq__(self, other):
        # Non-recursive equality check.
        for self_piece, other_piece in zip(self.flatten(), other.flatten()):
            if self_piece != other_piece:
                return False
        return True


class Apply(Ast):
    def __init__(self, function, argument):
        self.function = function
        self.argument = argument

    def _pieces(self):
        return [
            ("YIELD", (AstToken.OPEN_APPLY, None)),
            ("PROCESS", self.function),
            ("PROCESS", self.argument),
            ("YIELD", (AstToken.CLOSE_APPLY, None)),
        ]


class Name(Ast):
    def __init__(self, name):
        self.name = name

    def _pieces(self):
        return [
            ("YIELD", (AstToken.NAME, self.name)),
        ]


class Function(Ast):
    def __init__(self, name, body):
        self.name = name
        self.body = body

    def _pieces(self):
        return [
            ("YIELD", (AstToken.OPEN_FUNCTION, self.name)),
            ("PROCESS", self.body),
            ("YIELD", (AstToken.CLOSE_FUNCTION, None)),
        ]


class Definition(Ast):
    def __init__(self, name, arguments, body):
        self.name = name
        self.arguments = arguments
        self.body = body

    def _pieces(self):
        return [
            ("YIELD", (AstToken.OPEN_DEFINITION, self.name)),
            ("YIELD", (AstToken.DEFINITION_ARGS, self.arguments)),
            ("PROCESS", self.body),
        ]


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
    "identifier": "parse_expr_id",
    "left": "parse_expr_left",
    "right": "parse_expr_right",
    "slash": "parse_expr_slash",
    "dot": "parse_expr_dot",
    "end": "parse_expr_end",
    "equal": "parse_expr_fail",
    "atom": "parse_expr_atom",
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
            if token.type != "identifier":
                break
            names.append(token.value)
        if not names or token.type != "dot":
            raise ParseError("Invalid name sequence")
        self.values.append(names)

    def parse_expr_fail(self):
        raise ParseError("Invalid token: {}".format(self.token.value))

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
            raise ParseError("Unexpected end of input.")

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

    def parse_definition(self):
        """
        Parse a token stream into a definition.
        """
        # Parse function name.
        token = next(self.tokens)
        if token.type != "identifier":
            raise ParseError("Expected identifier")
        name = token.value

        # Parse argument names and equals.
        args = []
        token = next(self.tokens)
        while token.type == "identifier":
            args.append(token.value)
            token = next(self.tokens)

        if token.type != "equal":
            raise ParseError("Expected =")

        body = self.parse_expr()
        return Definition(name, args, body)

    def parse_name(self):
        """
        Parse a token stream into a single identifier.
        """
        token = next(self.tokens)
        if token.type != "identifier":
            raise ParseError("Expected identifier")
        name = token.value

        token = next(self.tokens)
        if token.type != "end":
            raise ParseError("Unexpected additional tokens")
        return name


def parse(tokens):
    return LambdaParser(TokenStream(tokens)).parse_expr()


def parse_definition(tokens):
    return LambdaParser(TokenStream(tokens)).parse_definition()


def parse_name(tokens):
    return LambdaParser(TokenStream(tokens)).parse_name()


class UnparseState(enum.Enum):
    """
    States used by unparse.
    """
    TOP = 0
    LEADING = 1
    TRAILING = 2
    MIDDLE = 3
    WRITE_LEFT = 4
    WRITE_RIGHT = 5


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
            raise TypeError("Unexpected expr of type {!r}".format(type(expr)))
    yield END_TOKEN
