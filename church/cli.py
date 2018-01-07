import cmd

from church.ast import ParseError
from church.eval import Environment, reduce, Suspension
from church.expr import (
    expr,
    Parameter,
    UndefinedNameError,
    unexpr,
)
from church.token import InvalidTerm, valid_id


def bindings_from_env(env):
    bindings = []
    while env is not None:
        var, env = env.var, env.env
        bindings.append((var.name, var))
    return bindings[::-1]


class LambdaCmd(cmd.Cmd):
    prompt = "(church) "

    def __init__(self, *args, **kwargs):
        super(LambdaCmd, self).__init__(*args, **kwargs)
        self.environment = None

    def emptyline(self):
        pass

    def do_exit(self, arg):
        """Leave the interpreter."""
        return True

    def _parse_term(self, value_expr):
        """
        Parse a given term.

        Returns a pair (success, term_or_message).
        """
        # Construct bindings from environment.
        # XXX Inefficient! Don't reconstruct every time!
        bindings = bindings_from_env(self.environment)

        try:
            term = expr(value_expr, bindings)
        except UndefinedNameError as e:
            name, = e.args
            return False,  "Undefined name: {!r}".format(name)
        except (InvalidTerm, ParseError) as e:
            return False, "Invalid syntax. {}".format(e)
        else:
            return True, term

    def do_def(self, arg):
        r"""Define a name for a lambda term.

        Example
        -------
        def two = \f x.f(f x)
        """
        pattern, equal, value_expr = arg.partition("=")
        pattern = pattern.strip()
        value_expr = value_expr.strip()

        if not pattern or not value_expr:
            self.stdout.write("Usage: def <name> <args> = <expr>\n")
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
            self.environment = Environment(
                var,
                Suspension(term, self.environment),
                self.environment,
            )

    def do_run(self, arg):
        r"""Evaluate a lambda term."""
        success, term_or_msg = self._parse_term(arg)
        if not success:
            msg = term_or_msg
            self.stdout.write(msg + "\n")
        else:
            term = term_or_msg
            result = reduce(term, self.environment)
            self.stdout.write("{}\n".format(unexpr(result)))
