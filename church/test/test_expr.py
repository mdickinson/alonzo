import unittest

from church.ast import parse
from church.expr import (
    ApplyExpr,
    bind,
    FunctionExpr,
    Parameter,
    ParameterReference,
)
from church.token import tokenize


class TestExpr(unittest.TestCase):
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
            with self.subTest(input):
                actual_expr = bind(parse(tokenize(input)))
                self.assertEqual(actual_expr, expected_expr)

    def test_bind_invalid(self):
        bad_inputs = [
            r"\x.y",
            r"(\x.x)x",
        ]
        for input in bad_inputs:
            with self.subTest(input):
                ast = parse(tokenize(input))
                with self.assertRaises(ValueError):
                    bind(ast)
