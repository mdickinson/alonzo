import unittest

from church.eval import reduce
from church.expr import expr


class TestEval(unittest.TestCase):
    def test_reduce_logic(self):
        id = expr(r"\x.x")
        true = expr(r"\x y.x")
        false = expr(r"\x y.y")
        pair = expr(r"\p q f.f p q")
        first = expr(r"\p.p\x y.x")
        second = expr(r"\p.p\x y.y")

        self.assertNotEqual(true, false)

        self.assertEqual(reduce(id), id)
        self.assertEqual(reduce(true), true)
        self.assertEqual(reduce(false), false)
        self.assertEqual(reduce(true @ false), expr(r"\a b c.c"))
        self.assertEqual(reduce(true @ false), expr(r"\a a a.a"))
        self.assertEqual(reduce(true @ true @ false), true)
        self.assertEqual(reduce(false @ true @ false), false)

        self.assertEqual(reduce(pair), pair)
        self.assertEqual(reduce(first @ (pair @ true @ false)), true)
        self.assertEqual(reduce(second @ (pair @ true @ false)), false)

    def test_reduce_arithmetic(self):
        test_expr = expr(r"\x.(\y.y)x")
        self.assertEqual(reduce(test_expr), expr(r"\x.x"))

        zero = expr(r"\f x.x")
        one = expr(r"\f x.f x")
        two = expr(r"\f x.f(f x)")
        three = expr(r"\f x.f(f(f x))")
        four = expr(r"\f x.f(f(f(f x)))")
        five = expr(r"\f x.f(f(f(f(f x))))")
        six = expr(r"\f x.f(f(f(f(f(f x)))))")

        succ = expr("\m f x.f(m f x)")

        add = expr(r"\m n f x.m f(n f x)")
        mul = expr(r"\m n f.m(n f)")
        pow = expr(r"\m n.n m")

        self.assertEqual(reduce(succ @ zero), one)
        self.assertEqual(reduce(succ @ one), two)
        self.assertEqual(reduce(succ @ two), three)
        self.assertEqual(reduce(succ @ three), four)

        self.assertEqual(reduce(add @ zero @ zero), zero)
        self.assertEqual(reduce(add @ zero @ one), one)
        self.assertEqual(reduce(add @ one @ zero), one)
        self.assertEqual(reduce(add @ one @ one), two)
        self.assertEqual(reduce(add @ one @ two), three)
        self.assertEqual(reduce(add @ two @ one), three)
        self.assertEqual(reduce(add @ two @ two), four)
        self.assertEqual(reduce(add @ two @ three), five)
        self.assertEqual(reduce(add @ three @ two), five)

        self.assertEqual(reduce(mul @ one @ zero), zero)
        self.assertEqual(reduce(mul @ one @ one), one)
        self.assertEqual(reduce(mul @ two @ two), four)
        self.assertEqual(reduce(mul @ two @ three), six)
        self.assertEqual(reduce(mul @ three @ two), six)

        self.assertEqual(reduce(pow @ two @ two), four)
        self.assertEqual(
            reduce(pow @ two @ three),
            reduce(mul @ two @ four),
        )
        self.assertEqual(
            reduce(pow @ three @ two),
            reduce(mul @ three @ three),
        )

    def test_reduce_deeply_nested(self):
        # Fails with a RecursionError for the recursive reduction algorithm.
        id = expr(r"\x.x")
        true = expr(r"\x y.x")

        nested = true
        for _ in range(3000):
            nested = id @ nested

        self.assertEqual(reduce(nested), true)
