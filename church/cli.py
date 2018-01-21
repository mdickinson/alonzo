"""
To do:

- catch KeyboardInterrupt while evaluating
- show all?
- show statistics
- fix up exception handling; decorator?

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
    definition,
    expr,
    name,
    unexpr,
)
from church.token import (
    TokenError,
)


INTRO_TEXT = """\
Welcome to the interactive lambda calculus interpreter.
Type 'help' to see supported commands.
"""


class LambdaCmd(cmd.Cmd):
    prompt = "(church) "

    intro = INTRO_TEXT

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
        r"""Leave the interpreter."""
        return True

    def do_let(self, arg):
        r"""Define a name for a lambda term.

        Examples
        --------
        let two = \f x.f(f x)
        let add m n = \f x.m f(n f x)
        let four = add two two
        """
        try:
            name, body = definition(arg, self.environment)
        except (UndefinedNameError, TokenError, ParseError) as e:
            self.stdout.write("{}\n".format(e))
            return

        self.environment = self.environment.append(
            name,
            Suspension(body, self.environment),
        )

    def do_eval(self, arg):
        r"""Evaluate a lambda term, reducing to normal form."""

        try:
            term = expr(arg, self.environment)
        except (UndefinedNameError, ParseError, TokenError) as e:
            self.stdout.write("{}\n".format(e))
            return

        result = reduce(term, self.environment)
        self.stdout.write("{}\n".format(unexpr(result)))

    def do_show(self, arg):
        r"""Show the definition of a previously defined name."""

        try:
            _, suspension = name(arg, self.environment)
        except (TokenError, ParseError):
            self.stdout.write("Usage: show <identifier>\n")
            return
        except UndefinedNameError as e:
            self.stdout.write("{}\n".format(e))
            return

        replacements = {
            parameter: parameter.name
            for parameter, _ in suspension.env
        }
        self.stdout.write("{}\n".format(unexpr(
            suspension.term, replacements)))
