"""
Evaluation strategies for lambda expressions.
"""
# XXX Rename ParameterReference to NameExpr.

from church.expr import (
    ApplyExpr, FunctionExpr, Parameter, ParameterReference,
)


class Suspension:
    def __init__(self, term, env):
        self.term = term
        self.env = env


def is_susp(obj):
    return type(obj) == Suspension


# Normal order reduction: translated from the paper
# "An Efficient Interpreter for the Lambda Calculus" by
# Luigia Aiello.

def mk_bind(var, val, env):
    env = env.copy()
    assert var not in env
    env[var] = val
    return env


def rtnf(term, lexenv):
    if type(term) == ParameterReference:
        return rtnf_var(term, lexenv)
    elif type(term) == ApplyExpr:
        return rtnf_app(term, lexenv)
    elif type(term) == FunctionExpr:
        return rtnf_lam(term, lexenv)
    else:
        raise ValueError("Unexpected term type: {}".format(
            type(term)))


def rtnf_var(var, lexenv):
    if var.parameter not in lexenv:
        # XXX When is this exercised? Do we need it? Should
        # we be wrapping var in a ParameterReference?
        return var
    else:
        susp = lexenv[var.parameter]
        if is_susp(susp):
            return rtnf(susp.term, susp.env)
        else:
            return susp


def rtnf_app(app, lexenv):
    susp = rtlf(app.function, lexenv)
    if is_susp(susp):
        fun = susp.term
        env = susp.env
        return rtnf(
            fun.body,
            mk_bind(
                fun.parameter,
                Suspension(app.argument, lexenv),
                env,
            )
        )
    else:
        return ApplyExpr(susp, rtnf(app.argument, lexenv))


def rtnf_lam(lam, lexenv):
    newvar = Parameter(lam.parameter.name)
    return FunctionExpr(
        newvar,
        rtnf(
            lam.body,
            mk_bind(lam.parameter, ParameterReference(newvar), lexenv),
        ),
    )


def rtlf(term, lexenv):
    if type(term) == ParameterReference:
        return rtlf_var(term, lexenv)
    elif type(term) == ApplyExpr:
        return rtlf_app(term, lexenv)
    elif type(term) == FunctionExpr:
        return rtlf_lam(term, lexenv)
    else:
        raise ValueError("Unexpected term type: {}".format(
            type(term)))


def rtlf_var(var, lexenv):
    if var.parameter not in lexenv:
        # Do we ever exercise this branch? Is this for
        # free variables?
        return var
    else:
        susp = lexenv[var.parameter]
        if is_susp(susp):
            return rtlf(susp.term, susp.env)
        else:
            return susp


def rtlf_app(app, lexenv):
    susp = rtlf(app.function, lexenv)
    if is_susp(susp):
        fun = susp.term
        env = susp.env
        return rtlf(
            fun.body,
            mk_bind(
                fun.parameter,
                Suspension(app.argument, lexenv),
                env,
            ),
        )
    else:
        return ApplyExpr(susp, rtnf(app.argument, lexenv))


def rtlf_lam(lam, lexenv):
    return Suspension(lam, lexenv)


def reduce(term):
    return rtnf(term, {})
