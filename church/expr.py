"""
Lambda expressions, complete with bindings from names to binding points.
"""
from church.ast import Apply, Function, Name


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


def flatten(expr):
    """
    Flatten an AST expression.

    Products a series of tokens, from:

      NAME, name
      OPEN_FUNCTION, name
      CLOSE_FUNCTION, None
      OPEN_APPLY, None
      CLOSE_APPLY, None
    """
    to_do = [(PROCESS, expr)]
    while to_do:
        action, arg = to_do.pop()
        if action == PROCESS:
            if type(arg) == Name:
                to_do.append((YIELD, (NAME, arg.name)))
            elif type(arg) == Apply:
                to_do.extend(
                    [
                        (YIELD, (CLOSE_APPLY, None)),
                        (PROCESS, arg.argument),
                        (PROCESS, arg.function),
                        (YIELD, (OPEN_APPLY, None)),
                    ]
                )
            elif type(arg) == Function:
                to_do.extend(
                    [
                        (YIELD, (CLOSE_FUNCTION, None)),
                        (PROCESS, arg.body),
                        (YIELD, (OPEN_FUNCTION, arg.name)),
                    ]
                )
            else:
                assert False, "never get here"
        elif action == YIELD:
            yield arg
        else:
            assert False, "never get here"


def bind(ast_expr):
    """
    Match names to function parameters in the given Ast instance.
    """
    expr_stack = []
    bindings = []

    for action, arg in flatten(ast_expr):
        if action == NAME:
            parameter = lookup(bindings, arg)
            expr_stack.append(
                ParameterReference(parameter)
            )
        elif action == OPEN_FUNCTION:
            parameter = Parameter(arg)
            bindings.append((arg, parameter))
        elif action == CLOSE_FUNCTION:
            name, parameter = bindings.pop()
            expr_stack.append(FunctionExpr(parameter, expr_stack.pop()))
        elif action == OPEN_APPLY:
            pass
        elif action == CLOSE_APPLY:
            arg = expr_stack.pop()
            fn = expr_stack.pop()
            expr_stack.append(ApplyExpr(fn, arg))
        else:
            assert False, "never get here"

    result = expr_stack.pop()
    assert len(expr_stack) == 0
    return result
