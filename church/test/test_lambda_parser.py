import unittest

from church.lambda_parser import Apply, Name, parse, ParseError


class TestLambdaParser(unittest.TestCase):
    def test_parse_simple_expressions(self):
        w, x, y, z = map(Name, "wxyz")
        self.assertEqual(parse("x"), x)
        self.assertEqual(parse("x y"), Apply(x, y))
        self.assertEqual(parse("x (y)"), Apply(x, y))
        self.assertEqual(parse("(x) y"), Apply(x, y))
        self.assertEqual(parse("(x)"), x)
        self.assertEqual(parse("((x))"), x)
        self.assertEqual(parse("x y z"), Apply(Apply(x, y), z))
        self.assertEqual(parse("(x y) z"), Apply(Apply(x, y), z))
        self.assertEqual(parse("x (y z)"), Apply(x, Apply(y, z)))
        self.assertEqual(parse("w x y z"), Apply(Apply(Apply(w, x), y), z))
        self.assertEqual(parse("(w x)(y z)"), Apply(Apply(w, x), Apply(y, z)))

    def test_parse_errors(self):
        bad_strings = [
            "",
            "(",
            ")",
            "()",
            "(x",
            "x (",
            "x )",
            ".",
            r"\x x",
        ]
        for bad_string in bad_strings:
            with self.assertRaises(ParseError):
                parse(bad_string)
