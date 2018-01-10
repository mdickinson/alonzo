"""
Evaluation strategies for lambda expressions.
"""
from church.expr import (
    ApplyExpr, FunctionExpr, NameExpr, Parameter,
)


# Normal order reduction: translated from section 4.2 of the paper "An
# Efficient Interpreter for the Lambda Calculus" by Luigia Aiello.

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
    """
    Look up the given binding in an environment.
    """
    # XXX Make this a method of a proper Environment class.
    while env is not None:
        if env.var == var:
            return env.val
        env = env.env
    raise LookupError("variable not in environment")


def apply(func, arg):
    """
    Apply a suspension of function type to an argument.
    """
    return Suspension(
        func.term.body,
        Environment(
            func.term.parameter,
            arg,
            func.env,
        ),
    )


def reduce(term, env=None):
    """
    Reduce the given term to its normal form, if that normal form exists.
    """
    to_do = [(0, Suspension(term, env))]
    results = []

    while to_do:
        action, arg = to_do.pop()
        if action < 2:
            term, lexenv = arg.term, arg.env
            if type(term) == NameExpr:
                susp = lookup(lexenv, term.parameter)
                if type(susp) == Suspension:
                    to_do.append((action, susp))
                else:
                    assert type(susp) == NameExpr
                    results.append(susp)
            elif type(term) == ApplyExpr:
                to_do.extend([
                    (action+2, Suspension(term.argument, lexenv)),
                    (1, Suspension(term.function, lexenv)),
                ])
            else:
                assert type(term) == FunctionExpr
                if action == 1:
                    results.append(arg)
                else:
                    newvar = Parameter(term.parameter.name)
                    results.append(newvar)
                    to_do.extend(
                        [(5, None), (0, apply(arg, NameExpr(newvar)))]
                    )

        elif action < 4:
            susp = results.pop()
            if type(susp) == Suspension:
                to_do.append((action-2, apply(susp, arg)))
            else:
                results.append(susp)
                to_do.extend([(4, None), (0, arg)])

        elif action == 4:
            argument, function = results.pop(), results.pop()
            results.append(ApplyExpr(function, argument))

        else:
            assert action == 5
            body, newvar = results.pop(), results.pop()
            results.append(FunctionExpr(newvar, body))

    result, = results
    return result
