"""
Tokenizing and untokenizing.
"""
import re


class Token:
    """
    Token class: a token has a type and a string value.
    """
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __eq__(self, other):
        return (
            self.type == other.type
            and self.value == other.value
        )


class TokenError(Exception):
    """
    Exception raised when a string can't be parsed into a stream of tokens.
    """
    pass


# Regex for tokenization.
TOKEN_REGEX = re.compile(
    "|".join(
        "(?P<{}>{})".format(groupname, regex)
        for groupname, regex in [
            ("whitespace", r"\s+"),
            ("identifier", r"\w+"),
            ("left", r"\("),
            ("right", r"\)"),
            ("dot", r"\."),
            ("equal", r"="),
            ("slash", r"\\"),
            ("end", r"\Z"),
            ("invalid", r"."),
        ]
    )
)


def tokenize(input):
    """
    Tokenize the given input string.

    Returns a generator that yields individual tokens.  Skips whitespace, and
    raises TokenError on invalid input.
    """
    for match in TOKEN_REGEX.finditer(input):
        token_type = match.lastgroup
        token_value = match.group(token_type)
        if token_type == "invalid":
            raise TokenError(
                "Invalid character in string: {!r}".format(token_value))
        elif token_type == "whitespace":
            pass
        else:
            yield Token(token_type, token_value)


def untokenize(tokens):
    """
    Reverse of tokenize, turning a token stream into a string.
    """
    output = []
    last_was_id = False
    for token in tokens:
        if token.type == "identifier":
            if last_was_id:
                output.append(" ")
            last_was_id = True
        else:
            last_was_id = False
        output.append(token.value)
    return ''.join(output)


# Convenience constants and functions for use in testing and
# untokenization.

#: Tokens consisting of a single punctuation character.
SINGLE_CHAR_TOKEN = {
    "(": Token("left", "("),
    ")": Token("right", ")"),
    "\\": Token("slash", "\\"),
    ".": Token("dot", "."),
    # Not used in lambda expressions, but used in let commands in the cli
    "=": Token("equal", "="),
}

#: Token used to mark the end of the stream.
END_TOKEN = Token("end", "")


#: Shortcut for creating an identifier token.
def ID_TOKEN(name):
    return Token("identifier", name)
