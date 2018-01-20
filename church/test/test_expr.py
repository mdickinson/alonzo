import unittest

from church.environment import (
    UndefinedNameError,
)
from church.expr import (
    ApplyExpr,
    expr,
    FunctionExpr,
    NameExpr,
    Parameter,
    unexpr,
)


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
        RX = NameExpr(X)
        RY = NameExpr(Y)
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
                with self.assertRaises(UndefinedNameError):
                    expr(input)

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
