r"""
Printing lambda terms.

a sequence without parentheses takes the form

   atom* lambda | atom+

so a recursive solution would be to:

- unwind the given term into a sequence

   fn arg1 arg2 ... argn

  (for some n >= 0)

- then render each piece:
  - any piece except the last that's a lambda needs parens
  - any non-atomic piece needs parens

Note that fn is either a name or a lambda, else we'd have expanded

Within parentheses, the same rules apply as at top level.

So at top level:




First let's ignore functions and just come up with
something non-recursive that works for applications.

Examples
--------
x -> "x"
Apply(x, y) -> "x y"
Apply(Apply(x, y), z) -> "x y z"
Apply(x, Apply(y, z)) -> "x (y z)"

How to achieve the above?

Imagine that we're flattening to a series of tokens:

Ex: for Apply(x, y), we have tokens: [Apply, Name, Name]

We construct a finite state machine ...

In *initial* state START:

- if we've got Name: output it and go to end
- if we've got Apply: move to new state APPLY

In state APPLY:

- given Name: output the name and move to state APPLY_ARG
- given APPLY: go to state APPLY again ...; on return,
  go to APPLY_ARG

In state APPLY_ARG:

- given Name, output the name and pop the stack...
- given Apply:
    - output "("
    - go to state APPLY, and on return, ...
    - output ")"
    - pop the stack ...

For lambdas, there's an ambiguity: given something of the form

  (x (\x.x)) x

we could write that either as

  (x\x.x)x

or

  x(\x.x)x

We'll go with the second form in this situation.


"""
from church.lambda_parser import Apply, Function, Name

# States
LEADING = "leading"
TOP = "top"  # top level, or just inside some parentheses.
TRAILING = "trailing"
MIDDLE = "middle"
NAMES = "names"

# Token types.
DOT = "dot"
END = "end"
ID = "id"
LEFT = "left"
RIGHT = "right"
SLASH = "slash"


def unparse(expr):
    """
    Unparse an expr into a sequence of tokens.
    """
    to_do = [(TOP, expr)]
    while to_do:
        state, expr = to_do.pop()
        if state == RIGHT:
            yield RIGHT, None
        elif state == LEFT:
            yield LEFT, None
        elif state == NAMES:
            yield SLASH, None
            for name in expr:
                yield ID, name
            yield DOT, None
        elif type(expr) == Name:
            yield ID, expr.name
        elif type(expr) == Apply:
            if state in {TOP, LEADING}:
                new_state = {TOP: TRAILING, LEADING: MIDDLE}[state]
                to_do.append((new_state, expr.argument))
                to_do.append((LEADING, expr.function))
            else:
                to_do.append((RIGHT, None))
                to_do.append((TOP, expr))
                to_do.append((LEFT, None))
        elif type(expr) == Function:
            if state in {TOP, TRAILING}:
                body, names = expr, []
                while type(body) == Function:
                    names.append(body.name)
                    body = body.body
                to_do.append((TOP, body))
                to_do.append((NAMES, names))
            else:
                to_do.append((RIGHT, None))
                to_do.append((TOP, expr))
                to_do.append((LEFT, None))
        else:
            assert False, "should never get here"
