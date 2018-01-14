"""
Lambda expressions, complete with bindings from names to binding points.
"""
import itertools

import church.ast as ast
from church.ast import AstToken, parse, unparse
from church.environment import environment
from church.token import tokenize, untokenize


class UndefinedNameError(Exception):
    pass


class Parameter:
    def __init__(self, name):
        self.name = name


class Expr:
    def flatten(self):
        """
        Convert an Expr into a series of tokens.
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

    def bitstring(self):
        """
        Convert an expr to its corresponding encoding as a bit string.
        """
        levels = {}
        bits = []
        for piece, arg in self.flatten():
            if piece == "APPLY":
                bits.append("01")
            elif piece == "FUNCTION":
                bits.append("00")
                assert arg not in levels
                levels[arg] = len(levels)
            elif piece == "CLOSE_FUNCTION":
                level = levels.pop(arg)
                assert level == len(levels)
            elif piece == "NAME":
                index = len(levels) - 1 - levels[arg]
                bits.append("1")
                bits.append("1" * index)
                bits.append("0")
        return ''.join(bits)

    def __eq__(self, other):
        return (
            type(self) == type(other)
            and self.bitstring() == other.bitstring()
        )

    def __matmul__(self, other):
        return ApplyExpr(self, other)


class ApplyExpr(Expr):
    def __init__(self, function, argument):
        self.function = function
        self.argument = argument

    def _pieces(self):
        return [
            ("YIELD", ("APPLY", None)),
            ("PROCESS", self.function),
            ("PROCESS", self.argument),
            ("YIELD", ("CLOSE_APPLY", None)),
        ]


class FunctionExpr(Expr):
    def __init__(self, parameter, body):
        self.parameter = parameter
        self.body = body

    def _pieces(self):
        return [
            ("YIELD", ("FUNCTION", self.parameter)),
            ("PROCESS", self.body),
            ("YIELD", ("CLOSE_FUNCTION", self.parameter)),
        ]


class NameExpr(Expr):
    def __init__(self, parameter):
        self.parameter = parameter

    def _pieces(self):
        return [
            ("YIELD", ("NAME", self.parameter)),
        ]


NAME = "name"
OPEN_FUNCTION = "open_function"
CLOSE_FUNCTION = "close_function"
OPEN_APPLY = "open_apply"
CLOSE_APPLY = "close_apply"

YIELD = "yield"
PROCESS = "process"


def bind(ast, env=None):
    """
    Match names to function parameters in the given Ast instance.
    """
    expr_stack = []

    if env is None:
        env = environment()

    for action, arg in ast.flatten():
        if action == AstToken.NAME:
            parameter, value = env.lookup_by_name(arg)
            if isinstance(value, NameExpr):
                # name added by this function
                expr_stack.append(value)
            else:
                # suspension from definition
                expr_stack.append(NameExpr(parameter))

        elif action == AstToken.OPEN_FUNCTION:
            parameter = Parameter(arg)
            expr_stack.append(parameter)
            value = NameExpr(parameter)
            env = env.append(parameter, value)
        elif action == AstToken.CLOSE_FUNCTION:
            env = env.pop()
            body = expr_stack.pop()
            parameter = expr_stack.pop()
            expr_stack.append(FunctionExpr(parameter, body))
        elif action == AstToken.OPEN_APPLY:
            pass
        elif action == AstToken.CLOSE_APPLY:
            arg = expr_stack.pop()
            fn = expr_stack.pop()
            expr_stack.append(ApplyExpr(fn, arg))
        else:
            raise RuntimeError("Unexpected action: {!r}".format(action))

    result, = expr_stack
    return result


DIGITS = "0123456789"


def variants(base_name):
    for suffix_length in itertools.count():
        for suffix in itertools.product(DIGITS, repeat=suffix_length):
            yield base_name + ''.join(suffix)


def name_avoiding(names_to_avoid, base_name):
    for variant in variants(base_name):
        if variant not in names_to_avoid:
            return variant


def unbind(expr, replacements=None):
    """
    Turn an Expr back into an AST expression, renaming names
    as we go to avoid potential clashes.
    """
    # Store for partially processed results.
    # Mapping from parameters to names to use in the AST.
    if replacements is None:
        replacements = {}
    # Parameter names currently in scope; these must be avoided
    # when choosing a new name.
    names_in_scope = set(replacements.values())

    result_stack = []
    for piece, arg in expr.flatten():
        if piece == "CLOSE_APPLY":
            argument = result_stack.pop()
            function = result_stack.pop()
            result_stack.append(ast.Apply(function, argument))
        elif piece == "FUNCTION":
            name = name_avoiding(names_in_scope, arg.name)
            assert name not in names_in_scope
            assert arg not in replacements
            names_in_scope.add(name)
            replacements[arg] = name
            result_stack.append(name)
        elif piece == "CLOSE_FUNCTION":
            body = result_stack.pop()
            name = result_stack.pop()
            result_stack.append(ast.Function(name, body))
            replacements.pop(arg)
            names_in_scope.remove(name)
        elif piece == "NAME":
            result_stack.append(ast.Name(replacements[arg]))

    result, = result_stack
    return result


def expr(input, env=None):
    return bind(parse(tokenize(input)), env)


def unexpr(expr, replacements=None):
    return untokenize(unparse(unbind(expr, replacements=replacements)))
