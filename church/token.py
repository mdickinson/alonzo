import enum
import string

#: Characters that are valid to use in an identifier.
IDENTIFIER_CHARACTERS = set(string.ascii_lowercase + string.digits + "_")

#: Characters that are valid whitespace.
WHITESPACE = set(" \n")


class TokenizationError(Exception):
    pass


class TokenType(enum.Enum):
    """
    Types of tokens.
    """
    # Tokens corresponding directly to text fragments.
    ID = enum.auto()
    LEFT = enum.auto()
    RIGHT = enum.auto()
    SLASH = enum.auto()
    DOT = enum.auto()

    # Pseudo-token used to indicate the end of the string.
    END = enum.auto()


class Token:
    """
    Token class: a token has a type and a string value.
    """
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __eq__(self, other):
        return (
            type(self) == type(other)
            and self.type == other.type
            and self.value == other.value
        )


#: Tokens consisting of a single punctuation character.
SINGLE_CHAR_TOKEN = {
    "(": Token(TokenType.LEFT, "("),
    ")": Token(TokenType.RIGHT, ")"),
    "\\": Token(TokenType.SLASH, "\\"),
    ".": Token(TokenType.DOT, "."),
}

#: Token used to mark the end of the stream.
END_TOKEN = Token(TokenType.END, "")


#: Shortcut for creating an identifier token.
def ID_TOKEN(name):
    return Token(TokenType.ID, name)


def valid_id(name):
    return name and set(name) <= IDENTIFIER_CHARACTERS


def tokenize(input):
    """
    Tokenize the given input, generating a stream of tokens.

    The token stream always finishes with a token of type END.
    """
    chars = iter(input)

    # Our tokenizer is a finite state machine with just two states: either
    # we're parsing an identifier, or we're not.
    parsing_id = False
    while True:
        c = next(chars, None)
        if c in IDENTIFIER_CHARACTERS:
            if not parsing_id:
                parsing_id = True
                id_chars = []
            id_chars.append(c)
        else:
            if parsing_id:
                name = ''.join(id_chars)
                yield ID_TOKEN(name)
                parsing_id = False
            if c in SINGLE_CHAR_TOKEN:
                yield SINGLE_CHAR_TOKEN[c]
            elif c in WHITESPACE:
                pass
            elif c is None:
                yield END_TOKEN
                break
            else:
                raise TokenizationError(
                    "Invalid character in string: {!r}".format(c))


def untokenize(tokens):
    """
    Reverse of tokenize, turning a token stream into a string.
    """
    output = []
    last_was_id = False
    for token in tokens:
        if token.type == TokenType.ID:
            if last_was_id:
                output.append(" ")
            last_was_id = True
        else:
            last_was_id = False
        output.append(token.value)
    return ''.join(output)
