import unittest

from church.lambda_parser import Apply, Function, Name, parse, ParseError


def expressions_equal(self, other):
    """
    Nonrecursive equality test, used for comparing deeply nested structures.
    """
    # List of pairs still to compare.
    to_compare = [(self, other)]
    while to_compare:
        expr0, expr1 = to_compare.pop()
        if type(expr0) != type(expr1):
            return False
        elif isinstance(expr0, Name):
            if expr0.name != expr1.name:
                return False
        elif isinstance(expr0, Function):
            if expr0.name != expr1.name:
                return False
            to_compare.append((expr0.body, expr1.body))
        elif isinstance(expr0, Apply):
            to_compare.append((expr0.argument, expr1.argument))
            to_compare.append((expr0.function, expr1.function))
        else:
            return False
    return True


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
            self.assertTrue(expressions_equal(parse(code), expr))

    def test_deeply_nested_constructs(self):
        # Check for performance problems and uses of Python recursion.
        x = Name("x")
        repeats = 20000

        # Pattern: "x x x x"
        code = "x" + " x"*repeats
        expected = x
        for _ in range(repeats):
            expected = Apply(expected, x)
        self.assertTrue(expressions_equal(parse(code), expected))

        # Pattern: "(((x)x)x)x"
        code = "("*repeats + "x" + ")x"*repeats
        expected = x
        for _ in range(repeats):
            expected = Apply(expected, x)
        self.assertTrue(expressions_equal(parse(code), expected))

        # Pattern: "x(x(x(x)))
        code = "x("*repeats + "x" + ")"*repeats
        expected = x
        for _ in range(repeats):
            expected = Apply(x, expected)
        self.assertTrue(expressions_equal(parse(code), expected))

        # Pattern: "\x.\x.\x.x"
        code = r"\x."*repeats + "x"
        expected = x
        for _ in range(repeats):
            expected = Function("x", expected)
        self.assertTrue(expressions_equal(parse(code), expected))

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
            r"\.x",
        ]
        for bad_string in bad_strings:
            with self.assertRaises(ParseError, msg=repr(bad_string)):
                parse(bad_string)
