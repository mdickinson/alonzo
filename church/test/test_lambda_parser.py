import unittest

from church.lambda_parser import Apply, Function, Name, parse, ParseError


class TestLambdaParser(unittest.TestCase):
    def test_parse_simple_expressions(self):
        w, x, y, z = map(Name, "wxyz")
        test_pairs = [
            ("x", x),
            ("x y", Apply(x, y)),
            ("x (y)", Apply(x, y)),
            ("(x (y))", Apply(x, y)),
            ("(x) y", Apply(x, y)),
            ("(x)", x),
            ("((x))", x),
            ("(((x)))", x),
            ("x y z", Apply(Apply(x, y), z)),
            ("(x y) z", Apply(Apply(x, y), z)),
            ("x (y z)", Apply(x, Apply(y, z))),
            ("w x y z", Apply(Apply(Apply(w, x), y), z)),
            ("(w x)(y z)", Apply(Apply(w, x), Apply(y, z))),

            (r"\x.x", Function("x", x)),
            (r"\x y.x", Function("x", Function("y", x))),
            (r"(\x y.x)", Function("x", Function("y", x))),
            (r"\x.x(y)", Function("x", Apply(x, y))),
            (r"\x.x\y.y", Function("x", Apply(x, Function("y", y)))),
            (r"\x y.x y", Function("x", Function("y", Apply(x, y)))),
            (r"\x.\y.x", Function("x", Function("y", x))),
            (r"\x y.(x)", Function("x", Function("y", x))),
            (r"\x.\y.x y", Function("x", Function("y", Apply(x, y)))),
            (r"\x.(\y.x)y", Function("x", Apply(Function("y", x), y))),
            (r"(\x.\y.x)y", Apply(Function("x", Function("y", x)), y)),
            (r"x\y.x", Apply(x, Function("y", x))),
            (r"(x\y.x)", Apply(x, Function("y", x))),
        ]
        for code, expr in test_pairs:
            self.assertEqual(parse(code), expr)

    def test_parse_errors(self):
        bad_strings = [
            "",
            "(",
            ")",
            "()",
            "(x",
            "(x.",
            "x)",
            "x(",
            ")x",
            ".",
            "x.",
            "(.",
            "\\",
            "\\\\",
            r"\(",
            r"\.",
            r"\)",
            r"\x x",
            r"\x\ ",
            r"\x(",
            r"\x)",
            r"\x.)",
            r"\x..",
            r"\x.",
            r"\x.x.",
        ]
        for bad_string in bad_strings:
            with self.assertRaises(ParseError, msg=repr(bad_string)):
                parse(bad_string)
