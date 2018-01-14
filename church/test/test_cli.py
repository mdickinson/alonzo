import io
import unittest

from church.cli import LambdaCmd


class TestCli(unittest.TestCase):
    def setUp(self):
        self.stdout = io.StringIO()
        self.cmd = LambdaCmd(stdout=self.stdout)

    def process_script(self, script):
        lines = iter(script.splitlines())
        stop = None
        while not stop:
            line = next(lines)
            line = self.cmd.precmd(line)
            stop = self.cmd.onecmd(line)
            stop = self.cmd.postcmd(stop, line)
        return self.stdout.getvalue()

    def test_cmd(self):
        test_script = r"""
let two = \f x.f(f x)
let add = \m n f x.m f(n f x)
let sum = add two two
eval sum
exit
"""
        output = self.process_script(test_script)
        self.assertEqual(output, r"\f x.f(f(f(f x)))""\n")

    def test_let_patterns(self):
        test_script = r"""
let two f x = f(f x)
let add m n = \f x.m f(n f x)
let sum = add two two
eval sum
exit
"""
        output = self.process_script(test_script)
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
        output = self.process_script(test_script)
        self.assertEqual(output, r"\f x.f(f(f(f(f(f x)))))""\n")

    def test_show(self):
        test_script = r"""
let two f x = f (f x)
show two
let pow m n = n m
let four = pow two two
show four
exit
"""
        output = self.process_script(test_script)
        output_lines = output.splitlines()
        self.assertEqual(len(output_lines), 2)
        self.assertEqual(output_lines[0], r"\f x.f(f x)")
        self.assertEqual(output_lines[1], r"pow two two")

    def test_multiple_bindings(self):
        # Check behaviour of multiple bindings using the same name:
        # we should be using lexical binding rather than dynamic binding.
        test_script = r"""
let n f x = f (f x)
let add m n = \f x.m f(n f x)
let four = add n n
let n f x = f (f (f x))  # this shouldn't affect the definition of 'four'
let six = add n n
eval four
eval six
exit
"""
        output = self.process_script(test_script)
        output_lines = output.splitlines()
        self.assertEqual(len(output_lines), 2)
        self.assertEqual(output_lines[0], r"\f x.f(f(f(f x)))")
        self.assertEqual(output_lines[1], r"\f x.f(f(f(f(f(f x)))))")
