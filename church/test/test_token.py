import unittest

from church.token import (
    END_TOKEN,
    ID_TOKEN,
    SINGLE_CHAR_TOKEN,
    tokenize,
    untokenize,
)

#: Shortcuts for ease of testing.
LEFT = SINGLE_CHAR_TOKEN["("]
RIGHT = SINGLE_CHAR_TOKEN[")"]
SLASH = SINGLE_CHAR_TOKEN["\\"]
DOT = SINGLE_CHAR_TOKEN["."]
ID = ID_TOKEN
END = END_TOKEN


class TestToken(unittest.TestCase):
    def test_tokenize(self):
        X = ID("x")
        Y = ID("y")
        XY = ID("xy")

        # Mapping from input to expected output.
        test_pairs = {
            "": [END],
            "x": [X, END],
            "xy": [XY, END],
            "x y": [X, Y, END],
            "x\ny": [X, Y, END],
            "x  \n  \n\ny": [X, Y, END],
            "(x)": [LEFT, X, RIGHT, END],
            "( xy xy )": [LEFT, XY, XY, RIGHT, END],
            "_ _ab ab_ a_b": [ID("_"), ID("_ab"), ID("ab_"), ID("a_b"), END],
            r"\x.x": [SLASH, X, DOT, X, END],
            r"\x y.x": [SLASH, X, Y, DOT, X, END],
        }

        for input, expected_tokens in test_pairs.items():
            with self.subTest(input=input):
                actual_tokens = list(tokenize(input))
                self.assertEqual(actual_tokens, expected_tokens)

    def test_non_ascii_input(self):
        # Non-ascii identifiers and whitespace should be permitted
        id1, id2 = "Μῆνιν", "ἄειδε"
        input = id1 + "\N{EN SPACE}" + id2
        self.assertEqual(list(tokenize(input)), [ID(id1), ID(id2), END])

    def test_untokenize(self):
        X = ID("x")
        test_pairs = [
            ([X, END], "x"),
            ([X, X, END], "x x"),
            ([X, X, X, END], "x x x"),
            ([LEFT, X, RIGHT, END], "(x)"),
            ([LEFT, X, RIGHT, X, END], "(x)x"),
            ([X, LEFT, X, RIGHT, END], "x(x)"),
            ([SLASH, X, DOT, X], "\\x.x"),
            ([SLASH, X, X, DOT, X], "\\x x.x"),
        ]
        for tokens, expected_output in test_pairs:
            with self.subTest(expected_output=expected_output):
                actual_output = untokenize(tokens)
                self.assertEqual(actual_output, expected_output)

    def test_roundtrip(self):
        test_inputs = [
            "x",
            "x y",
            "(x)",
            "(x y)",
            "\\x.x",
            "\\x xyz.x",
            "\\x.x xyz",
            "\\first.\\second.first second",
        ]
        for input in test_inputs:
            self.assertEqual(untokenize(tokenize(input)), input)
