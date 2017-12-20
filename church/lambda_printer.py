import enum

from church.lambda_parser import Apply, Function, Name
from church.token import END_TOKEN, ID_TOKEN, SINGLE_CHAR_TOKEN


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
