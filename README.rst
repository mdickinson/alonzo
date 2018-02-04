The **church** package gives an interpreter for untyped lambda calculus.

Here's an example session::

    $ python -m church
    Welcome to the interactive lambda calculus interpreter.
    Type 'help' to see supported commands.

    (church) let two = \f x.f(f x)
    (church) let add m n = \f x.m f(n f x)
    (church) show add
    \m n f x.m f(n f x)
    (church) let four = add two two
    (church) show four
    add two two
    (church) eval four
    \f x.f(f(f(f x)))
    (church) exit
