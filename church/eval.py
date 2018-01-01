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

def reduce_iterative(term):
    # (REDUCE_TERM, term, lexenv): _reduce(term, lexenv, False)
    # (REDUCE_FUNCTION, term, lexenv): _reduce(term, lexenv, True)
    to_do = [("REDUCE_TERM", term, None)]
    results = []

    while to_do:
        action, *args = to_do.pop()
        if action == "REDUCE_TERM":
            term, lexenv = args
            if type(term) == NameExpr:
                susp = lookup(lexenv, term.parameter)
                if type(susp) == Suspension:
                    to_do.append(("REDUCE_TERM", susp.term, susp.env))
                elif type(susp) == NameExpr:
                    results.append(susp)
                else:
                    raise TypeError(
                        "Unexpected suspension type: {!r}".format(type(susp)))
            elif type(term) == ApplyExpr:
                to_do.append(("REDUCE_ARGUMENT", term.argument, lexenv))
                to_do.append(("REDUCE_FUNCTION", term.function, lexenv))
            elif type(term) == FunctionExpr:
                newvar = Parameter(term.parameter.name)
                newenv = Environment(term.parameter, NameExpr(newvar), lexenv)
                to_do.append(("BUILD_FUNCTION", newvar))
                to_do.append(("REDUCE_TERM", term.body, newenv))
            else:
                raise TypeError(
                    "Unexpected term type: {!r}".format(type(term)))

        elif action == "REDUCE_FUNCTION":
            term, lexenv = args
            if type(term) == NameExpr:
                susp = lookup(lexenv, term.parameter)
                if type(susp) == Suspension:
                    to_do.append(("REDUCE_FUNCTION", susp.term, susp.env))
                elif type(susp) == NameExpr:
                    results.append(susp)
                else:
                    raise TypeError(
                        "Unexpected suspension type: {!r}".format(type(susp)))
            elif type(term) == ApplyExpr:
                to_do.append(("REDUCE_ARGUMENT1", term.argument, lexenv))
                to_do.append(("REDUCE_FUNCTION", term.function, lexenv))
            elif type(term) == FunctionExpr:
                results.append(Suspension(term, lexenv))
            else:
                raise TypeError(
                    "Unexpected term type: {!r}".format(type(term)))

        elif action == "REDUCE_ARGUMENT":
            term, lexenv = args
            susp = results.pop()
            if type(susp) == Suspension:
                newenv = Environment(
                    susp.term.parameter,
                    Suspension(term, lexenv),
                    susp.env,
                )
                to_do.append(("REDUCE_TERM", susp.term.body, newenv))
            else:
                assert type(susp) in {NameExpr, ApplyExpr}
                results.append(susp)
                to_do.append(("BUILD_APPLICATION",))
                to_do.append(("REDUCE_TERM", term, lexenv))

        elif action == "REDUCE_ARGUMENT1":
            term, lexenv = args
            susp = results.pop()
            if type(susp) == Suspension:
                newenv = Environment(
                    susp.term.parameter,
                    Suspension(term, lexenv),
                    susp.env,
                )
                to_do.append(("REDUCE_FUNCTION", susp.term.body, newenv))
            else:
                assert type(susp) in {NameExpr, ApplyExpr}
                results.append(susp)
                to_do.append(("BUILD_APPLICATION",))
                to_do.append(("REDUCE_TERM", term, lexenv))

        elif action == "BUILD_FUNCTION":
            newvar, = args
            results.append(FunctionExpr(newvar, results.pop()))

        elif action == "BUILD_APPLICATION":
            argument = results.pop()
            function = results.pop()
            results.append(ApplyExpr(function, argument))

        else:
            raise RuntimeError("Bad action: {!r}".format(action))

    assert len(results) == 1
    return results.pop()


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
            newenv = Environment(
                susp.term.parameter,
                Suspension(term.argument, lexenv),
                susp.env,
            )
            return _reduce(susp.term.body, newenv, to_lambda=to_lambda)
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
            newenv = Environment(term.parameter, NameExpr(newvar), lexenv)
            return FunctionExpr(
                newvar,
                _reduce(term.body, newenv, to_lambda=False),
            )

    else:
        raise TypeError(
            "Unexpected term type: {!r}".format(type(term)))


def reduce_recursive(term):
    return _reduce(term, None, to_lambda=False)


reduce = reduce_iterative
