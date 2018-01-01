"""
Evaluation strategies for lambda expressions.
"""
from church.expr import (
    ApplyExpr, FunctionExpr, NameExpr, Parameter,
)


# A suspension combines an unnormalised term with the environment it
# should be normalised in.

class Suspension:
    def __init__(self, term, env):
        self.term = term
        self.env = env


# An environment represents a mapping to from Parameter instances to either
# NameExpr instances or Suspension instances.

class Environment:
    def __init__(self, var, val, env):
        self.var = var
        self.val = val
        self.env = env


def lookup(env, var):
    while env is not None:
        if env.var == var:
            return env.val
        env = env.env
    raise LookupError("variable not in environment")


# Normal order reduction: translated from the paper
# "An Efficient Interpreter for the Lambda Calculus" by
# Luigia Aiello.

def _reduce(term, lexenv, to_lambda):
    """
    Reduce a given lambda expression to its normal form (if it exists).
    """
    if type(term) == NameExpr:
        susp = lookup(lexenv, term.parameter)
        if type(susp) == Suspension:
            return _reduce(susp.term, susp.env, to_lambda=to_lambda)
        elif type(susp) == NameExpr:
            return susp
        else:
            raise TypeError(
                "Unexpected suspension type: {!r}".format(type(susp)))
    elif type(term) == ApplyExpr:
        susp = _reduce(term.function, lexenv, to_lambda=True)
        if type(susp) == Suspension:
            return _reduce(
                susp.term.body,
                Environment(
                    susp.term.parameter,
                    Suspension(term.argument, lexenv),
                    susp.env,
                ),
                to_lambda=to_lambda,
            )
        else:
            return ApplyExpr(
                susp,
                _reduce(term.argument, lexenv, to_lambda=False),
            )
    elif type(term) == FunctionExpr:
        if to_lambda:
            return Suspension(term, lexenv)
        else:
            newvar = Parameter(term.parameter.name)
            return FunctionExpr(
                newvar,
                _reduce(
                    term.body,
                    Environment(
                        term.parameter,
                        NameExpr(newvar),
                        lexenv,
                    ),
                    to_lambda=False,
                ),
            )
    else:
        raise TypeError(
            "Unexpected term type: {!r}".format(type(term)))


def reduce(term):
    return _reduce(term, None, to_lambda=False)
