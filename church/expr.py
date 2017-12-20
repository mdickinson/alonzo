"""
Lambda expressions, complete with bindings from names to binding points.
"""
from church.ast import AstToken


class Parameter:
    def __init__(self, name):
        self.name = name


def lookup(bindings, name):
    for parameter_name, parameter in reversed(bindings):
        if parameter_name == name:
            return parameter
    raise ValueError("Failed lookup")


class Expr:
    def flatten(self, bindings=None):
        """
        Convert an Expr into a series of tokens.
        """
        if bindings is None:
            bindings = {}

        # TODO non-recursive version
        if type(self) == ApplyExpr:
            yield ("APPLY", None)
            yield from self.function.flatten(bindings)
            yield from self.argument.flatten(bindings)
        elif type(self) == FunctionExpr:
            assert self.parameter not in bindings
            bindings[self.parameter] = len(bindings)
            yield ("FUNCTION", None)
            yield from self.body.flatten(bindings)
            bindings.pop(self.parameter)
        elif type(self) == ParameterReference:
            index = len(bindings) - 1 - bindings[self.parameter]
            yield ("INDEX", index)

    def __eq__(self, other):
        if type(self) != type(other):
            return False

        for self_piece, other_piece in zip(self.flatten(), other.flatten()):
            if self_piece != other_piece:
                return False
        return True


class ApplyExpr(Expr):
    def __init__(self, function, argument):
        if not isinstance(function, Expr):
            raise TypeError("function should be an instance of Expr")
        if not isinstance(argument, Expr):
            raise TypeError("argument should be an instance of Expr")
        self.function = function
        self.argument = argument


class FunctionExpr(Expr):
    def __init__(self, parameter, body):
        if not isinstance(body, Expr):
            raise TypeError("body should be an instance of Expr")
        if not isinstance(parameter, Parameter):
            raise TypeError("parameter should be an instance of Parameter")
        self.parameter = parameter
        self.body = body


class ParameterReference(Expr):
    def __init__(self, parameter):
        if not isinstance(parameter, Parameter):
            raise TypeError("parameter should be an instance of Parameter")
        self.parameter = parameter


NAME = "name"
OPEN_FUNCTION = "open_function"
CLOSE_FUNCTION = "close_function"
OPEN_APPLY = "open_apply"
CLOSE_APPLY = "close_apply"

YIELD = "yield"
PROCESS = "process"


def bind(ast_expr):
    """
    Match names to function parameters in the given Ast instance.
    """
    expr_stack = []
    bindings = []

    for action, arg in ast_expr.flatten():
        if action == AstToken.NAME:
            parameter = lookup(bindings, arg)
            expr_stack.append(
                ParameterReference(parameter)
            )
        elif action == AstToken.OPEN_FUNCTION:
            parameter = Parameter(arg)
            bindings.append((arg, parameter))
        elif action == AstToken.CLOSE_FUNCTION:
            name, parameter = bindings.pop()
            expr_stack.append(FunctionExpr(parameter, expr_stack.pop()))
        elif action == AstToken.OPEN_APPLY:
            pass
        elif action == AstToken.CLOSE_APPLY:
            arg = expr_stack.pop()
            fn = expr_stack.pop()
            expr_stack.append(ApplyExpr(fn, arg))
        else:
            assert False, "never get here"

    result = expr_stack.pop()
    assert len(expr_stack) == 0
    return result
