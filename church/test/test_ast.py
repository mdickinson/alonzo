import unittest

from church.ast import (
    Apply,
    Definition,
    Function,
    Name,
    parse,
    parse_definition,
    ParseError,
    unparse,
)
from church.token import (
    END_TOKEN, ID_TOKEN, SINGLE_CHAR_TOKEN, tokenize, untokenize)

#: Shortcuts for ease of testing.
LEFT = SINGLE_CHAR_TOKEN["("]
RIGHT = SINGLE_CHAR_TOKEN[")"]
SLASH = SINGLE_CHAR_TOKEN["\\"]
DOT = SINGLE_CHAR_TOKEN["."]
ID = ID_TOKEN
END = END_TOKEN


class TestParse(unittest.TestCase):
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
            (r"x(\y.y)z", Apply(Apply(x, Function("y", y)), z)),
            (r"(x\y.y)z", Apply(Apply(x, Function("y", y)), z)),
        ]
        for code, expr in test_pairs:
            with self.subTest(code=code):
                self.assertEqual(parse(tokenize(code)), expr)

    def test_parse_deeply_nested_constructs(self):
        # Check for performance problems and uses of Python recursion.
        x = Name("x")
        repeats = 20000

        # Pattern: "x x x x"
        code = "x" + " x"*repeats
        expected = x
        for _ in range(repeats):
            expected = Apply(expected, x)
        self.assertEqual(parse(tokenize(code)), expected)

        # Pattern: "(((x)x)x)x"
        code = "("*repeats + "x" + ")x"*repeats
        expected = x
        for _ in range(repeats):
            expected = Apply(expected, x)
        self.assertEqual(parse(tokenize(code)), expected)

        # Pattern: "x(x(x(x)))
        code = "x("*repeats + "x" + ")"*repeats
        expected = x
        for _ in range(repeats):
            expected = Apply(x, expected)
        self.assertEqual(parse(tokenize(code)), expected)

        # Pattern: "\x.\x.\x.x"
        code = r"\x."*repeats + "x"
        expected = x
        for _ in range(repeats):
            expected = Function("x", expected)
        self.assertEqual(parse(tokenize(code)), expected)

        # Pattern: "\x x x.x".
        code = r"\x" + " x"*(repeats-1) + ".x"
        expected = x
        for _ in range(repeats):
            expected = Function("x", expected)
        self.assertEqual(parse(tokenize(code)), expected)

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
            "x = y",
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
                parse(tokenize(bad_string))

    def test_unparse(self):
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
            with self.subTest(test_expr=test_expr):
                expr = parse(tokenize(test_expr))
                actual_tokens = list(unparse(expr))
                self.assertEqual(actual_tokens, expected_tokens)

    def test_roundtrip(self):
        pairs = {
            "x": "x",
            "abc def": "abc def",
            "(abc def)": "abc def",
            r"\x.\y.y x": r"\x y.y x",
            "(x x)x": "x x x",
            "x (x x)": "x(x x)",
        }
        for input, expected_output in pairs.items():
            with self.subTest(input=input):
                actual_output = untokenize(unparse(parse(tokenize(input))))
                self.assertEqual(actual_output, expected_output)

    def test_equality(self):
        x, y = map(Name, "xy")

        self.assertEqual(x, x)
        self.assertEqual(Apply(x, y), Apply(x, y))
        self.assertEqual(Function("x", x), Function("x", x))

        self.assertNotEqual(Name("x"), Name("y"))
        self.assertNotEqual(
            Apply(Apply(x, y), Apply(x, x)),
            Apply(Apply(x, x), Apply(x, x)),
        )
        self.assertNotEqual(Function("x", x), Function("y", y))

    def test_parse_definition(self):
        f, m, n, x, y = map(Name, "fmnxy")
        test_pairs = [
            ("f = x y", Definition("f", [], Apply(x, y))),
            ("f arg1 = x", Definition("f", ["arg1"], x)),
            (
                r"add m n = \f x.m f(n f x)",
                Definition(
                    "add", ["m", "n"],
                    Function(
                        "f",
                        Function(
                            "x",
                            Apply(Apply(m, f), Apply(Apply(n, f), x)),
                        )
                    ),
                ),
            )
        ]

        for code, definition in test_pairs:
            with self.subTest(code=code):
                self.assertEqual(parse_definition(tokenize(code)), definition)

    def test_parse_bad_definitions(self):
        bad_definitions = [
            "f x y",
            "= x y",
            "f x = ((((x)))",
        ]
        for code in bad_definitions:
            with self.assertRaises(ParseError):
                parse_definition(tokenize(code))
