"""
To do:

- catch KeyboardInterrupt while evaluating
- add intro text
- show all?
- show statistics

"""
import cmd

from church.ast import ParseError
from church.environment import (
    UndefinedNameError,
)
from church.eval import (
    environment,
    reduce,
    Suspension,
)
from church.expr import (
    expr,
    Parameter,
    unexpr,
)
# XXX Shouldn't need valid_id.
from church.token import (
    TokenizationError,
    tokenize,
    TokenType,
    valid_id,
)


class LambdaCmd(cmd.Cmd):
    prompt = "(church) "

    def __init__(self, *args, **kwargs):
        super(LambdaCmd, self).__init__(*args, **kwargs)
        self.environment = environment()

    def emptyline(self):
        pass

    def precmd(self, line):
        # Strip off any comment.
        line, *_ = line.partition('#')
        return line.strip()

    def do_exit(self, arg):
        """Leave the interpreter."""
        return True

    def _parse_term(self, value_expr):
        """
        Parse a given term.

        Returns a pair (success, term_or_message).
        """
        try:
            term = expr(value_expr, self.environment)
        except UndefinedNameError as e:
            return False, "Undefined name: {}".format(*e.args)
        except (TokenizationError, ParseError) as e:
            return False, "Invalid syntax. {}".format(e)
        else:
            return True, term

    def do_let(self, arg):
        r"""Define a name for a lambda term.

        Example
        -------
        let two = \f x.f(f x)
        """
        pattern, equal, value_expr = arg.partition("=")
        pattern = pattern.strip()
        value_expr = value_expr.strip()

        if not pattern or not value_expr:
            self.stdout.write("Usage: let <name> <args> = <expr>\n")
            return

        pieces = pattern.split()
        for piece in pieces:
            if not valid_id(piece):
                self.stdout.write("Invalid name: {!r}\n".format(piece))
                return

        varname, *args = pieces
        if args:
            value_expr = "\{}.{}".format(' '.join(args), value_expr)

        if not valid_id(varname):
            self.stdout.write("Invalid name: {!r}\n".format(varname))
            return

        var = Parameter(varname)
        success, term_or_msg = self._parse_term(value_expr)

        if not success:
            msg = term_or_msg
            self.stdout.write(msg + "\n")
        else:
            term = term_or_msg
            self.environment = self.environment.append(
                var,
                Suspension(term, self.environment),
            )

    def do_eval(self, arg):
        r"""Evaluate a lambda term, reducing to normal form."""
        success, term_or_msg = self._parse_term(arg)
        if not success:
            msg = term_or_msg
            self.stdout.write(msg + "\n")
        else:
            term = term_or_msg
            result = reduce(term, self.environment)
            self.stdout.write("{}\n".format(unexpr(result)))

    def _parse_show_arg(self, arg):
        """
        Parse an argument to a 'show' command.

        Raises ParseError on failure.
        """
        # Move to ast.py?

        # XXX Need to catch tokenization errors, too.
        tokens = tokenize(arg)
        id_token = next(tokens)
        if id_token.type != TokenType.ID:
            raise ParseError("Not an identifier: {!r}".format(arg))
        end_token = next(tokens)
        if end_token.type != TokenType.END:
            raise ParseError(
                "Unexpected characters after identifier: {!r}".format(arg))
        return id_token.value

    def do_show(self, arg):
        r"""Show the definition of a previously defined name."""

        try:
            id = self._parse_show_arg(arg)
        except (TokenizationError, ParseError):
            self.stdout.write("Usage: show <identifier>\n")
            return

        try:
            _, suspension = self.environment.lookup_by_name(id)
        except UndefinedNameError as e:
            self.stdout.write("Undefined name: {}\n".format(*e.args))
            return

        replacements = {
            parameter: parameter.name
            for parameter, _ in suspension.env
        }
        self.stdout.write("{}\n".format(unexpr(
            suspension.term, replacements)))
