import unittest

from church.lambda_parser import parse
from church.lambda_printer import unparse, ID, LEFT, RIGHT, SLASH, DOT


class TestLambdaPrinter(unittest.TestCase):
    def test_nonclosed_expressions(self):
        pairs = [
            ("x", [ID]),
            ("x x", [ID, ID]),
            ("x x x", [ID, ID, ID]),
            ("x(x x)", [ID, LEFT, ID, ID, RIGHT]),
            ("((x x)x)x", [ID, ID, ID, ID]),
            ("x(x(x x))", [ID, LEFT, ID, LEFT, ID, ID, RIGHT, RIGHT]),
            ("(x(x x))x", [ID, LEFT, ID, ID, RIGHT, ID]),
            ("(x x)(x x)", [ID, ID, LEFT, ID, ID, RIGHT]),
            ("x(x x x)", [ID, LEFT, ID, ID, ID, RIGHT]),
            (r"\x.x", [SLASH, ID, DOT, ID]),
            (r"\x.x x", [SLASH, ID, DOT, ID, ID]),
            (r"(\x.x)x", [LEFT, SLASH, ID, DOT, ID, RIGHT, ID]),
            (r"x \x.x", [ID, SLASH, ID, DOT, ID]),
            (r"x(\x.x)x", [ID, LEFT, SLASH, ID, DOT, ID, RIGHT, ID]),
            (r"\x x.x x", [SLASH, ID, ID, DOT, ID, ID]),
        ]

        for test_expr, token_types in pairs:
            expr = parse(test_expr)
            self.assertEqual(
                [token_type for token_type, token_value in unparse(expr)],
                token_types,
            )
