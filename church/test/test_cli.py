import io
import unittest

from church.cli import LambdaCmd


class TestCli(unittest.TestCase):
    def setUp(self):
        self.stdout = io.StringIO()
        self.cmd = LambdaCmd(stdout=self.stdout)

    def process_lines(self, lines):
        lines = iter(lines)
        stop = None
        while not stop:
            line = next(lines)
            line = self.cmd.precmd(line)
            stop = self.cmd.onecmd(line)
            stop = self.cmd.postcmd(stop, line)

    def test_cmd(self):
        test_script = r"""
let two = \f x.f(f x)
let add = \m n f x.m f(n f x)
let sum = add two two
eval sum
exit
"""
        self.process_lines(test_script.splitlines())
        output = self.stdout.getvalue()
        self.assertEqual(output, r"\f x.f(f(f(f x)))""\n")

    def test_let_patterns(self):
        test_script = r"""
let two f x = f(f x)
let add m n = \f x.m f(n f x)
let sum = add two two
eval sum
exit
"""
        self.process_lines(test_script.splitlines())
        output = self.stdout.getvalue()
        self.assertEqual(output, r"\f x.f(f(f(f x)))""\n")

    def test_comments(self):
        test_script = r"""
let two f x = f (f x)  # can define functions using patterns
let three = \f x.f(f(f x))  # or using lambda notation, \x.x
let mul m n = \f.m (n f)  # or a mixture of both
eval mul two three  # comments are supported everywhere!
# even on otherwise blank lines!

      # and indented, too.

      # a second # character has no # effect

exit# time to say goodbye

"""
        self.process_lines(test_script.splitlines())
        output = self.stdout.getvalue()
        self.assertEqual(output, r"\f x.f(f(f(f(f(f x)))))""\n")
