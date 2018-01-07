import io
import unittest

from church.cli import LambdaCmd


class TestCli(unittest.TestCase):
    def test_cmd(self):
        stdout = io.StringIO()
        cmd = LambdaCmd(stdout=stdout)

        test_script = r"""
def two = \f x.f(f x)
def add = \m n f x.m f(n f x)
def sum = add two two
run sum
"""
        for line in test_script.splitlines():
            if line.strip():
                cmd.onecmd(line)

        output = stdout.getvalue()
        self.assertEqual(output, r"\f x.f(f(f(f x)))""\n")

    def test_def_patterns(self):
        stdout = io.StringIO()
        cmd = LambdaCmd(stdout=stdout)

        test_script = r"""
def two f x = f(f x)
def add m n = \f x.m f(n f x)
def sum = add two two
run sum
"""
        for line in test_script.splitlines():
            if line.strip():
                cmd.onecmd(line)

        output = stdout.getvalue()
        self.assertEqual(output, r"\f x.f(f(f(f x)))""\n")
