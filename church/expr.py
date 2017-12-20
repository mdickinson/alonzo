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
    def flatten(self):
        """
        Convert an Expr into a series of tokens.
        """
        bindings = {}
        to_do = [("PROCESS", self)]
        while to_do:
            action, arg = to_do.pop()
            if action == "PROCESS":
                if type(arg) == ApplyExpr:
                    yield "APPLY", None
                    to_do.append(("PROCESS", arg.argument))
                    to_do.append(("PROCESS", arg.function))
                elif type(arg) == FunctionExpr:
                    yield "FUNCTION", None
                    assert arg.parameter not in bindings
                    bindings[arg.parameter] = len(bindings)
                    to_do.append(("POP_BINDING", arg.parameter))
                    to_do.append(("PROCESS", arg.body))
                elif type(arg) == ParameterReference:
                    index = len(bindings) - 1 - bindings[arg.parameter]
                    yield "INDEX", index
            elif action == "POP_BINDING":
                index = bindings.pop(arg)
                assert index == len(bindings)

        assert not bindings

    def bitstring(self):
        """
        Convert an expr to its corresponding encoding as a bit string.
        """
        PIECE_TO_BITS = {
            "APPLY": "01",
            "FUNCTION": "00",
            "INDEX": "1",
        }

        bits = []
        for piece, arg in self.flatten():
            bits.append(PIECE_TO_BITS[piece])
            if piece == "INDEX":
                bits.extend(["1"*arg, "0"])
        return ''.join(bits)

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
