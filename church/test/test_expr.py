import unittest

from church.ast import parse, unparse
from church.expr import (
    ApplyExpr,
    bind,
    FunctionExpr,
    Parameter,
    ParameterReference,
    unbind,
)
from church.token import tokenize, untokenize


def expr(input):
    return bind(parse(tokenize(input)))


def unexpr(expr):
    return untokenize(unparse(unbind(expr)))


def harmonious_names(expr):
    """
    Return True if no parameter name matches the parameter name from
    any enclosing scope.
    """
    names = set()
    for piece, arg in expr.flatten():
        if piece == "FUNCTION":
            if arg.name in names:
                return False
            names.add(arg.name)
        elif piece == "CLOSE_FUNCTION":
            names.remove(arg.name)
    return True


class TestExpr(unittest.TestCase):
    def test_equal(self):
        test_equal_pairs = [
            (r"\x.x", r"\dummy.dummy"),
            (r"\x x.x", r"\x y.y"),
            (r"\x x.x", r"\x.\x.x"),
            (r"\x y x y.x", r"\a b c d.c"),
        ]

        for first, second in test_equal_pairs:
            with self.subTest(first=first, second=second):
                first_expr = expr(first)
                second_expr = expr(second)
                self.assertEqual(first_expr, second_expr)

        test_unequal_pairs = [
            (r"\x.x", r"\x.x x"),
            (r"\x.\x.x", r"\y.\x.y"),
        ]
        for first, second in test_unequal_pairs:
            with self.subTest(first=first, second=second):
                first_expr = expr(first)
                second_expr = expr(second)
                self.assertNotEqual(first_expr, second_expr)

    def test_bind(self):
        X = Parameter("x")
        Y = Parameter("y")
        RX = ParameterReference(X)
        RY = ParameterReference(Y)
        test_pairs = {
            r"\x.x": FunctionExpr(X, RX),
            r"\x x.x": FunctionExpr(X, FunctionExpr(Y, RY)),
            r"\x.\x.x": FunctionExpr(X, FunctionExpr(Y, RY)),
            r"\x.x x": FunctionExpr(X, ApplyExpr(RX, RX)),
            r"\x.x x x": FunctionExpr(X, ApplyExpr(ApplyExpr(RX, RX), RX)),
            r"\x.(\x.x)x": FunctionExpr(X, ApplyExpr(FunctionExpr(Y, RY), RX)),
        }

        for input, expected_expr in test_pairs.items():
            with self.subTest(input=input):
                actual_expr = expr(input)
                self.assertEqual(actual_expr, expected_expr)

    def test_bind_invalid(self):
        bad_inputs = [
            r"\x.y",
            r"(\x.x)x",
        ]
        for input in bad_inputs:
            with self.subTest(input=input):
                ast = parse(tokenize(input))
                with self.assertRaises(ValueError):
                    bind(ast)

    def test_bitstring(self):
        test_pairs = {
            r"\x.x": "0010",
            r"\x y.y": "000010",
            r"\x y.x": "0000110",
            r"\x.x x": "00011010",
            r"\x x y.y": "00000010",
        }
        for input, expected_bitstring in test_pairs.items():
            with self.subTest(input=input):
                actual_expr = expr(input)
                actual_bitstring = actual_expr.bitstring()
                self.assertEqual(actual_bitstring, expected_bitstring)

    def test_call(self):
        # Triples function, argument, result.
        test_triples = [
            (r"\x.x", r"\x.x", r"\x.x"),
            (r"\x.x", r"\x.x x", r"\x.x x"),
        ]
        for fn, arg, expected_result in test_triples:
            fn_expr = expr(fn)
            arg_expr = expr(arg)
            result_expr = expr(expected_result)

            actual_result = fn_expr(arg_expr)
            self.assertEqual(actual_result, result_expr)

        true = expr(r"\x y.x")
        false = expr(r"\x y.y")

        self.assertEqual(true(true)(false), true)
        self.assertEqual(false(true)(false), false)

    def test_unbind(self):
        test_inputs = [
            r"\x.x",
            r"\x x.x",
            r"\x x x.x",
            r"\x y x y.x y",
        ]
        for input in test_inputs:
            with self.subTest(input=input):
                original_expr = expr(input)
                str_expr = unexpr(original_expr)
                self.assertEqual(expr(str_expr), original_expr)
