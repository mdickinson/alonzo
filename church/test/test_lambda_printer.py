import unittest

from church.lambda_parser import parse
from church.lambda_printer import unparse
from church.token import END_TOKEN, ID_TOKEN, SINGLE_CHAR_TOKEN

#: Shortcuts for ease of testing.
LEFT = SINGLE_CHAR_TOKEN["("]
RIGHT = SINGLE_CHAR_TOKEN[")"]
SLASH = SINGLE_CHAR_TOKEN["\\"]
DOT = SINGLE_CHAR_TOKEN["."]
ID = ID_TOKEN
END = END_TOKEN


class TestLambdaPrinter(unittest.TestCase):
    def test_nonclosed_expressions(self):
        X = ID("x")
        pairs = [
            ("x", [X, END]),
            ("x x", [X, X, END]),
            ("x x x", [X, X, X, END]),
            ("x(x x)", [X, LEFT, X, X, RIGHT, END]),
            ("((x x)x)x", [X, X, X, X, END]),
            ("x(x(x x))", [X, LEFT, X, LEFT, X, X, RIGHT, RIGHT, END]),
            ("(x(x x))x", [X, LEFT, X, X, RIGHT, X, END]),
            ("(x x)(x x)", [X, X, LEFT, X, X, RIGHT, END]),
            ("x(x x x)", [X, LEFT, X, X, X, RIGHT, END]),
            (r"\x.x", [SLASH, X, DOT, X, END]),
            (r"\x.x x", [SLASH, X, DOT, X, X, END]),
            (r"(\x.x)x", [LEFT, SLASH, X, DOT, X, RIGHT, X, END]),
            (r"x \x.x", [X, SLASH, X, DOT, X, END]),
            (r"x(\x.x)x", [X, LEFT, SLASH, X, DOT, X, RIGHT, X, END]),
            (r"\x x.x x", [SLASH, X, X, DOT, X, X, END]),
        ]

        for test_expr, expected_tokens in pairs:
            with self.subTest(test_expr):
                expr = parse(test_expr)
                actual_tokens = list(unparse(expr))
                self.assertEqual(actual_tokens, expected_tokens)
